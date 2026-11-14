from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Quiz(models.Model):
    DIFFICULTIES = [("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")]
    THEMES = [(t, t.title()) for t in ("violet", "coral", "blue", "green", "amber", "pink")]

    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="quizzes")
    description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTIES, default="medium")
    seconds_per_question = models.PositiveSmallIntegerField(default=30)
    emoji = models.CharField(max_length=8, default="🧠")
    theme = models.CharField(max_length=10, choices=THEMES, default="violet")
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "quizzes"
        ordering = ["id"]

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    code = models.TextField(blank=True, help_text="Optional code snippet shown under the question.")
    explanation = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text[:70]


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class Result(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="results")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="results")
    score = models.PositiveSmallIntegerField()
    total = models.PositiveSmallIntegerField()
    time_taken = models.PositiveIntegerField(default=0, help_text="Seconds")
    answers = models.JSONField(default=dict)  # {question_id: chosen_option_id or null}
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.quiz} ({self.score}/{self.total})"

    @property
    def percentage(self):
        return round(100 * self.score / self.total) if self.total else 0

    @property
    def headline(self):
        p = self.percentage
        if p >= 90:
            return "Outstanding"
        if p >= 70:
            return "Nice work"
        if p >= 40:
            return "Getting there"
        return "Keep practicing"
