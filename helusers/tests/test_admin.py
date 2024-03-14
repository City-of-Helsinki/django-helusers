import pytest
from django.contrib.auth import get_user_model
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
    UserSocialAuth.objects.create(user=admin_user, provider=TunnistamoOIDCAuth.name)
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
