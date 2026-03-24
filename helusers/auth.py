from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()


class HelusersModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Conditionally disable password authentication of the default ModelBackend.

        When the HELUSERS_PASSWORD_LOGIN_DISABLED setting is True, password-based
        authentication is disabled for all users except those whose usernames are
        listed in HELUSERS_PASSWORD_LOGIN_ALLOWLIST.
        """
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        if getattr(
            settings, "HELUSERS_PASSWORD_LOGIN_DISABLED", False
        ) and username not in getattr(
            settings, "HELUSERS_PASSWORD_LOGIN_ALLOWLIST", []
        ):
            return None

        return super().authenticate(request, username, password, **kwargs)
