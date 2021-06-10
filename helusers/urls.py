"""URLs module"""
from django.urls import path
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.views.decorators.csrf import csrf_exempt
from . import views


app_name = "helusers"

urlpatterns = []

if (
    "social_django" in settings.INSTALLED_APPS
    and "helusers.tunnistamo_oidc.TunnistamoOIDCAuth"
    in settings.AUTHENTICATION_BACKENDS
):
    if not settings.LOGOUT_REDIRECT_URL:
        raise ImproperlyConfigured(
            "LOGOUT_REDIRECT_URL setting must be set to use social_auth login/logout with helusers."
        )

    urlpatterns.extend(
        [
            path("logout/", views.LogoutView.as_view(), name="auth_logout"),
            path(
                "logout/complete/",
                views.LogoutCompleteView.as_view(),
                name="auth_logout_complete",
            ),
            path("login/", views.LoginView.as_view(), name="auth_login"),
        ]
    )


if getattr(settings, "HELUSERS_BACK_CHANNEL_LOGOUT_ENABLED", False):
    urlpatterns.extend(
        [
            path(
                "logout/oidc/backchannel/",
                csrf_exempt(views.OIDCBackChannelLogout.as_view()),
            ),
        ]
    )
