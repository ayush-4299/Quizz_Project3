from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("quiz/<slug:slug>/", views.quiz_detail, name="quiz_detail"),
    path("quiz/<slug:slug>/play/", views.play, name="play"),
    path("results/<int:pk>/", views.result_detail, name="result"),
    path("history/", views.history, name="history"),
    path("api/quiz/<slug:slug>/questions/", views.api_questions, name="api_questions"),
    path("api/quiz/<slug:slug>/check/", views.api_check, name="api_check"),
    path("api/quiz/<slug:slug>/submit/", views.api_submit, name="api_submit"),
]
