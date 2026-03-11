import pytest
from django.contrib.auth import get_user_model

from helusers.auth import HelusersModelBackend

USERNAME = "testuser"
PASSWORD = "testpassword"


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        username=USERNAME,
        password=PASSWORD,
    )


@pytest.fixture
def backend():
    return HelusersModelBackend()


@pytest.mark.django_db
def test_password_login_allowed_by_default(user, backend):
    result = backend.authenticate(request=None, username=USERNAME, password=PASSWORD)
    assert result == user


@pytest.mark.django_db
def test_password_login_disabled_when_setting_is_true(user, backend, settings):
    settings.HELUSERS_PASSWORD_LOGIN_DISABLED = True
    result = backend.authenticate(request=None, username=USERNAME, password=PASSWORD)
    assert result is None


@pytest.mark.django_db
def test_password_login_allowed_when_setting_is_false(user, backend, settings):
    settings.HELUSERS_PASSWORD_LOGIN_DISABLED = False
    result = backend.authenticate(request=None, username=USERNAME, password=PASSWORD)
    assert result == user
