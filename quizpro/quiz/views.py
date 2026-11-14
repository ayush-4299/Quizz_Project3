import json
import random
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .models import Category, Question, Quiz, Result


# ---------- helpers ----------
def api_login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Log in to continue."}, status=401)
        return view(request, *args, **kwargs)
    return wrapper


def _body(request):
    try:
        data = json.loads(request.body or b"{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _published(slug):
    return get_object_or_404(Quiz.objects.select_related("category"), slug=slug, is_published=True)


# ---------- pages ----------
def home(request):
    quizzes = (Quiz.objects.filter(is_published=True)
               .select_related("category")
               .annotate(num_questions=Count("questions", distinct=True)))
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("c", "").strip()
    if q:
        quizzes = quizzes.filter(Q(title__icontains=q) | Q(description__icontains=q)
                                 | Q(category__name__icontains=q))
    if cat:
        quizzes = quizzes.filter(category__slug=cat)
    categories = Category.objects.filter(quizzes__is_published=True).distinct()
    return render(request, "quiz/home.html", {
        "quizzes": quizzes, "categories": categories, "q": q, "active_cat": cat,
    })


def quiz_detail(request, slug):
    quiz = _published(slug)
    best = {}
    for r in quiz.results.select_related("user").order_by("-score", "time_taken")[:500]:
        best.setdefault(r.user_id, r)
    leaderboard = list(best.values())[:10]
    my_best = None
    if request.user.is_authenticated:
        my_best = quiz.results.filter(user=request.user).order_by("-score", "time_taken").first()
    return render(request, "quiz/detail.html", {
        "quiz": quiz, "total": quiz.questions.count(),
        "leaderboard": leaderboard, "my_best": my_best,
    })


@login_required
def play(request, slug):
    quiz = _published(slug)
    total = quiz.questions.count()
    if not total:
        raise Http404("This quiz has no questions yet.")
    return render(request, "quiz/play.html", {"quiz": quiz, "total": total})


@login_required
def result_detail(request, pk):
    result = get_object_or_404(Result.objects.select_related("quiz"), pk=pk, user=request.user)
    rows = []
    for q in result.quiz.questions.prefetch_related("options"):
        options = list(q.options.all())
        correct = next((o for o in options if o.is_correct), None)
        chosen_id = result.answers.get(str(q.id))
        chosen = next((o for o in options if o.id == chosen_id), None)
        rows.append({"question": q, "correct": correct, "chosen": chosen,
                     "is_correct": bool(chosen and correct and chosen.id == correct.id)})
    return render(request, "quiz/result.html", {"result": result, "rows": rows})


@login_required
def history(request):
    results = list(request.user.results.select_related("quiz")[:50])
    stats = {
        "attempts": len(results),
        "average": round(sum(r.percentage for r in results) / len(results)) if results else 0,
        "best": max((r.percentage for r in results), default=0),
    }
    return render(request, "quiz/history.html", {"results": results, "stats": stats})


# ---------- JSON API used by static/js/play.js ----------
@api_login_required
@require_GET
def api_questions(request, slug):
    quiz = _published(slug)
    payload = []
    for q in quiz.questions.prefetch_related("options"):
        options = [{"id": o.id, "text": o.text} for o in q.options.all()]
        random.shuffle(options)  # correct flag is never sent to the browser
        payload.append({"id": q.id, "text": q.text, "code": q.code, "options": options})
    return JsonResponse({"title": quiz.title, "seconds": quiz.seconds_per_question, "questions": payload})


@api_login_required
@require_POST
def api_check(request, slug):
    quiz = _published(slug)
    body = _body(request)
    qid = _int(body.get("question_id"))
    if qid is None:
        return JsonResponse({"error": "Invalid question."}, status=400)
    question = get_object_or_404(Question.objects.prefetch_related("options"), pk=qid, quiz=quiz)
    chosen = _int(body.get("option_id"))
    correct = next((o for o in question.options.all() if o.is_correct), None)
    return JsonResponse({
        "correct": bool(correct and chosen == correct.id),
        "correct_option_id": correct.id if correct else None,
        "explanation": question.explanation,
    })


@api_login_required
@require_POST
def api_submit(request, slug):
    """Scores the attempt on the server so the result can't be tampered with."""
    quiz = _published(slug)
    body = _body(request)
    answers = body.get("answers") if isinstance(body.get("answers"), dict) else {}
    time_taken = min(max(_int(body.get("time_taken")) or 0, 0), 86400)

    score, stored = 0, {}
    questions = list(quiz.questions.prefetch_related("options"))
    for q in questions:
        options = {o.id: o for o in q.options.all()}
        chosen = _int(answers.get(str(q.id)))
        if chosen in options:
            stored[str(q.id)] = chosen
            score += 1 if options[chosen].is_correct else 0
        else:
            stored[str(q.id)] = None
    result = Result.objects.create(user=request.user, quiz=quiz, score=score,
                                   total=len(questions), time_taken=time_taken, answers=stored)
    return JsonResponse({"result_id": result.id, "url": reverse("result", args=[result.id])})
