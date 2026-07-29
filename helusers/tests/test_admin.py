from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.test import Client, override_settings
from django.urls import reverse
from pytest_django.asserts import assertContains
from social_django.models import UserSocialAuth

from helusers.tunnistamo_oidc import TunnistamoOIDCAuth


@pytest.fixture
def admin_user():
    return get_user_model().objects.create_superuser(
        username="admin",
        email="admin@example.com",
        first_name="Admin",
        password="super-duper-test",
    )


def test_admin_index(client):
    response = client.get(reverse("admin:index"), follow=True)

    assert response.status_code == 200
    assertContains(
        response, "Kirjaudu sisään Helsingin kaupungin työntekijän tunnuksella"
    )
    assertContains(response, '<form method="post" action="/helauth/login/">')
    assertContains(
        response,
        '<input type="hidden" name="csrfmiddlewaretoken"',
    )
    assertContains(
        response,
        '<input type="hidden" name="next" value="/admin/">',
    )


@pytest.mark.django_db
def test_django_admin_login_post_preserves_request(client):
    response = client.post(
        reverse("helusers:auth_login"),
        data={"next": "/admin/", "ui_locales": "en"},
    )

    assert response.status_code == 307
    assert response.url == (
        "/pysocial/login/tunnistamo/?next=%2Fadmin%2F&ui_locales=en"
    )


@pytest.mark.django_db
def test_django_admin_login_get_is_not_allowed(client):
    response = client.get(
        reverse("helusers:auth_login"),
        data={"next": "/admin/", "ui_locales": "en"},
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_django_admin_login_post_reaches_social_auth(client):
    with mock.patch(
        "social_django.views.do_auth",
        return_value=HttpResponse(status=204),
    ) as do_auth:
        response = client.post(
            reverse("helusers:auth_login"),
            data={"next": "/admin/"},
            follow=True,
        )

    assert response.status_code == 204
    assert response.redirect_chain == [
        ("/pysocial/login/tunnistamo/?next=%2Fadmin%2F", 307)
    ]
    request = do_auth.call_args.args[0].strategy.request
    assert request.method == "POST"
    assert request.POST["next"] == "/admin/"


@pytest.mark.django_db
@override_settings(
    CSRF_USE_SESSIONS=True,
    MIDDLEWARE=[
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
    ],
)
def test_django_admin_login_post_preserves_session_csrf():
    client = Client(enforce_csrf_checks=True)
    response = client.get(reverse("admin:index"), follow=True)
    csrf_token = get_token(response.wsgi_request)

    with mock.patch(
        "social_django.views.do_auth",
        return_value=HttpResponse(status=204),
    ) as do_auth:
        response = client.post(
            reverse("helusers:auth_login"),
            data={"next": "/admin/", "csrfmiddlewaretoken": csrf_token},
            follow=True,
        )

    assert response.status_code == 204
    assert do_auth.call_args.args[0].strategy.request.method == "POST"


@pytest.mark.django_db
def test_admin_app_name(client, admin_user):
    """The App name in the admin index page"""
    client.login(username="admin", password="super-duper-test")

    response = client.get(reverse("admin:index"))

    assert response.status_code == 200
    assertContains(response, "Helsinki Users")


@pytest.mark.django_db
def test_django_admin_logout(client, admin_user):
    """Test that the Django admin logout works.

    helusers.admin_site.AdminSite expects the end session url to be in the session
    for using the helusers.views.LogoutView
    """
    expected_url = "http://example.com/redirected_after_logout"
    UserSocialAuth.objects.create(
        user=admin_user, provider=TunnistamoOIDCAuth.name, uid="12345"
    )
    client.login(username="admin", password="super-duper-test")
    session = client.session
    session["social_auth_end_session_url"] = expected_url
    session.save()

    response = client.get(reverse("admin:index"))
    assert response.status_code == 200
    assert response.wsgi_request.user.is_authenticated

    response = client.post(reverse("admin:logout"))
    assert response.status_code == 302
    assert response.url == expected_url
    assert response.wsgi_request.user.is_anonymous
