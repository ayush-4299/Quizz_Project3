from django.conf import settings


def site(request):
    return {"GOOGLE_ENABLED": bool(settings.GOOGLE_CLIENT_ID)}
