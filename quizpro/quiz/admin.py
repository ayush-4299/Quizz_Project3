from django import forms
from django.contrib import admin
from django.forms.models import BaseInlineFormSet

from .models import Category, Option, Question, Quiz, Result


class OptionFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        filled = correct = 0
        for form in self.forms:
            data = getattr(form, "cleaned_data", None)
            if not data or data.get("DELETE") or not data.get("text"):
                continue
            filled += 1
            correct += 1 if data.get("is_correct") else 0
        if filled < 2:
            raise forms.ValidationError("Add at least two options.")
        if correct != 1:
            raise forms.ValidationError("Mark exactly one option as correct.")


class OptionInline(admin.TabularInline):
    model = Option
    formset = OptionFormSet
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "order")
    list_filter = ("quiz",)
    search_fields = ("text",)
    inlines = [OptionInline]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "difficulty", "is_published")
    list_filter = ("category", "difficulty", "is_published")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("user", "quiz", "score", "total", "time_taken", "created_at")
    list_filter = ("quiz",)
