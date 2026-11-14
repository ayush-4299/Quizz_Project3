from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from quiz.models import Category, Option, Question, Quiz
from quiz.seed_data import QUIZZES


class Command(BaseCommand):
    help = "Load the starter technical quizzes (safe to run more than once)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Rebuild the questions of quizzes that already exist.")

    @transaction.atomic
    def handle(self, *args, **opts):
        for data in QUIZZES:
            category, _ = Category.objects.get_or_create(
                name=data["category"], defaults={"slug": slugify(data["category"])})
            quiz, created = Quiz.objects.update_or_create(slug=data["slug"], defaults={
                "title": data["title"], "category": category, "description": data["description"],
                "difficulty": data["difficulty"], "seconds_per_question": data["seconds"],
                "emoji": data["emoji"], "theme": data["theme"], "is_published": True,
            })
            if quiz.questions.exists():
                if not opts["reset"]:
                    self.stdout.write(f"Skipped {quiz.title} (already has questions)")
                    continue
                quiz.questions.all().delete()
            for order, item in enumerate(data["questions"], start=1):
                question = Question.objects.create(
                    quiz=quiz, text=item["text"], code=item["code"],
                    explanation=item["why"], order=order)
                Option.objects.bulk_create([
                    Option(question=question, text=text, is_correct=(i == item["answer"]))
                    for i, text in enumerate(item["options"])])
            self.stdout.write(self.style.SUCCESS(f"Loaded {quiz.title}: {len(data['questions'])} questions"))
