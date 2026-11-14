import os
from pathlib import Path
import dj_database_url
BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=""):
    return os.environ.get(name, default)


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = env("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [
    "quizz-project3.vercel.app",
    "quizz-project3-32lvzlav9-ayush-4299s-projects.vercel.app",
    "localhost",
    "127.0.0.1",
]
CSRF_TRUSTED_ORIGINS = [
    "https://quizz-project3.vercel.app",
    "https://quizz-project3-32lvzlav9-ayush-4299s-projects.vercel.app",
]
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "quiz",
]
SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "quiz.context_processors.site",
    ]},
}]



DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True
    )
}
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication (django-allauth)
LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True
GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = env("GOOGLE_CLIENT_SECRET")
SOCIALACCOUNT_PROVIDERS = {"google": {
    "SCOPE": ["profile", "email"],
    "AUTH_PARAMS": {"access_type": "online"},
}}
if GOOGLE_CLIENT_ID:
    SOCIALACCOUNT_PROVIDERS["google"]["APP"] = {
        "client_id": GOOGLE_CLIENT_ID,
        "secret": GOOGLE_CLIENT_SECRET,
        "key": "",
    }
