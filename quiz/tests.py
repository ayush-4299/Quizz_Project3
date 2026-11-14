import json

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Option, Question, Quiz, Result


class QuizFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_quizzes", verbosity=0)
        cls.user = get_user_model().objects.create_user("ayush", "a@example.com", "pass12345!")

    def setUp(self):
        self.client.force_login(self.user)
        self.quiz = Quiz.objects.get(slug="python-fundamentals")

    def post(self, name, data):
        return self.client.post(reverse(name, args=[self.quiz.slug]), json.dumps(data),
                                content_type="application/json")

    def test_seed_creates_five_quizzes_with_fifty_questions(self):
        self.assertEqual(Quiz.objects.count(), 5)
        self.assertEqual(Question.objects.count(), 50)
        for q in Question.objects.all():
            self.assertEqual(q.options.filter(is_correct=True).count(), 1)

    def test_seed_is_idempotent(self):
        call_command("seed_quizzes", verbosity=0)
        self.assertEqual(Question.objects.count(), 50)

    def test_pages_render(self):
        for url in ["/", f"/quiz/{self.quiz.slug}/", f"/quiz/{self.quiz.slug}/play/", "/history/"]:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.client.logout()  # allauth redirects logged-in users away from these pages
        for url in ["/accounts/login/", "/accounts/signup/"]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_play_requires_login(self):
        self.client.logout()
        r = self.client.get(f"/quiz/{self.quiz.slug}/play/")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.client.get(f"/api/quiz/{self.quiz.slug}/questions/").status_code, 401)

    def test_questions_api_hides_answers(self):
        data = self.client.get(f"/api/quiz/{self.quiz.slug}/questions/").json()
        self.assertEqual(len(data["questions"]), 10)
        self.assertNotIn("is_correct", json.dumps(data))

    def test_check_and_submit_scores_on_server(self):
        answers = {}
        for i, q in enumerate(self.quiz.questions.all()):
            correct = q.options.get(is_correct=True)
            wrong = q.options.filter(is_correct=False).first()
            r = self.post("api_check", {"question_id": q.id, "option_id": correct.id}).json()
            self.assertTrue(r["correct"])
            answers[str(q.id)] = correct.id if i < 7 else wrong.id  # 7 right, 3 wrong
        res = self.post("api_submit", {"answers": answers, "time_taken": 42}).json()
        result = Result.objects.get(pk=res["result_id"])
        self.assertEqual((result.score, result.total, result.percentage), (7, 10, 70))
        self.assertEqual(self.client.get(res["url"]).status_code, 200)

    def test_submit_ignores_foreign_options_and_bad_input(self):
        other = Option.objects.exclude(question__quiz=self.quiz).first()
        q = self.quiz.questions.first()
        res = self.post("api_submit", {"answers": {str(q.id): other.id}, "time_taken": "x"}).json()
        self.assertEqual(Result.objects.get(pk=res["result_id"]).score, 0)
        self.assertEqual(self.post("api_check", {"question_id": "abc"}).status_code, 400)

    def test_results_are_private(self):
        res = self.post("api_submit", {"answers": {}, "time_taken": 1}).json()
        other = get_user_model().objects.create_user("other", password="pass12345!")
        self.client.force_login(other)
        self.assertEqual(self.client.get(res["url"]).status_code, 404)
