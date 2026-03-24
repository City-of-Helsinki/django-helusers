from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend as DjangoModelBackend

from helusers.auth import HelusersModelBackend

USERNAME = "testuser"
EMAIL = "user@example.com"
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


@pytest.mark.django_db
def test_allowlisted_user_can_login_when_password_login_disabled(
    user, backend, settings
):
    settings.HELUSERS_PASSWORD_LOGIN_DISABLED = True
    settings.HELUSERS_PASSWORD_LOGIN_ALLOWLIST = [USERNAME]
    result = backend.authenticate(request=None, username=USERNAME, password=PASSWORD)
    assert result == user


@pytest.mark.django_db
def test_non_allowlisted_user_cannot_login_when_password_login_disabled(
    user, backend, settings
):
    settings.HELUSERS_PASSWORD_LOGIN_DISABLED = True
    settings.HELUSERS_PASSWORD_LOGIN_ALLOWLIST = ["other_user"]
    result = backend.authenticate(request=None, username=USERNAME, password=PASSWORD)
    assert result is None


@pytest.mark.django_db
def test_empty_allowlist_does_not_allow_login_when_password_login_disabled(
    user, backend, settings
):
    settings.HELUSERS_PASSWORD_LOGIN_DISABLED = True
    settings.HELUSERS_PASSWORD_LOGIN_ALLOWLIST = []
    result = backend.authenticate(request=None, username=USERNAME, password=PASSWORD)
    assert result is None


@pytest.mark.django_db
def test_allowlist_has_no_effect_when_password_login_not_disabled(
    user, backend, settings
):
    settings.HELUSERS_PASSWORD_LOGIN_DISABLED = False
    settings.HELUSERS_PASSWORD_LOGIN_ALLOWLIST = [USERNAME]
    result = backend.authenticate(request=None, username=USERNAME, password=PASSWORD)
    assert result == user


# Tests for the username kwargs fallback (supports custom user models where
# USERNAME_FIELD differs from 'username').


@pytest.mark.django_db
def test_username_falls_back_to_kwargs_when_username_param_is_none(user, backend):
    """When username=None, backend retrieves it from kwargs[USERNAME_FIELD]."""
    with mock.patch("helusers.auth.UserModel") as mock_model:
        mock_model.USERNAME_FIELD = "email"
        with mock.patch.object(
            DjangoModelBackend, "authenticate", return_value=user
        ) as mock_super:
            result = backend.authenticate(request=None, email=EMAIL, password=PASSWORD)
    mock_super.assert_called_once_with(None, EMAIL, PASSWORD, email=EMAIL)
    assert result == user


@pytest.mark.django_db
def test_allowlist_check_uses_username_from_kwargs(user, backend, settings):
    """When password login is disabled, allowlist is checked against username from kwargs."""
    settings.HELUSERS_PASSWORD_LOGIN_DISABLED = True
    settings.HELUSERS_PASSWORD_LOGIN_ALLOWLIST = [EMAIL]
    with mock.patch("helusers.auth.UserModel") as mock_model:
        mock_model.USERNAME_FIELD = "email"
        with mock.patch.object(DjangoModelBackend, "authenticate", return_value=user):
            result = backend.authenticate(request=None, email=EMAIL, password=PASSWORD)
    assert result == user


@pytest.mark.django_db
def test_non_allowlisted_user_from_kwargs_blocked_when_login_disabled(
    user, backend, settings
):
    """When password login is disabled, a user from kwargs not in the allowlist is blocked."""
    settings.HELUSERS_PASSWORD_LOGIN_DISABLED = True
    settings.HELUSERS_PASSWORD_LOGIN_ALLOWLIST = [f"other_{EMAIL}"]
    with mock.patch("helusers.auth.UserModel") as mock_model:
        mock_model.USERNAME_FIELD = "email"
        with mock.patch.object(DjangoModelBackend, "authenticate", return_value=user):
            result = backend.authenticate(request=None, email=EMAIL, password=PASSWORD)
    assert result is None
