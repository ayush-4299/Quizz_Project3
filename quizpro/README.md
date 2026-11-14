# QuizPro

A full-stack quiz app built with **Django, JavaScript, HTML, CSS and SQLite**, with Google OAuth, user registration/login, five technical quizzes (50 MCQs) and a Wayground-style interface.

## Features
- Google sign-in (django-allauth) plus email/username registration and login
- Quiz categories with 5 starter technical quizzes: Python, JavaScript, SQL, Data Structures & Algorithms, Django
- Models: `User`, `Category`, `Quiz`, `Question`, `Option`, `Result` (Django ORM, SQLite)
- Timed play screen: per-question countdown, instant right/wrong feedback with explanations, streak counter, question navigator, keyboard shortcuts (A-D or 1-4, Enter, arrows)
- Scores are calculated on the server when you submit, so the saved result can't be edited from the browser
- Result review page, personal history, and a per-quiz leaderboard
- Admin site to add your own quizzes (each question must have exactly one correct option)

## Run it locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_quizzes
python manage.py createsuperuser        # optional, for /admin/
python manage.py runserver
```
Open http://127.0.0.1:8000/

Run the tests with `python manage.py test`.

## Turn on Google sign-in
1. In Google Cloud Console, open **APIs & Services > Credentials** and create an **OAuth client ID** (Web application).
2. Add this Authorized redirect URI: `http://127.0.0.1:8000/accounts/google/login/callback/`
   (use your real domain too when you deploy).
3. Set the environment variables, then restart the server:
   ```bash
   export GOOGLE_CLIENT_ID="your-id.apps.googleusercontent.com"
   export GOOGLE_CLIENT_SECRET="your-secret"
   ```
The "Continue with Google" button appears automatically once `GOOGLE_CLIENT_ID` is set.

## Add more quizzes
Use `/admin/`, or add entries to `quiz/seed_data.py` and run `python manage.py seed_quizzes` (use `--reset` to rebuild existing quizzes).

## Project layout
```
config/            settings, urls
quiz/              models, views (pages + JSON API), admin, seed data, tests
templates/         base, quiz pages, allauth login/signup overrides
static/css/app.css Wayground-style theme
static/js/play.js  quiz player
```
