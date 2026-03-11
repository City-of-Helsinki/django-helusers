from django.conf import settings
from django.contrib.auth.backends import ModelBackend


class HelusersModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Disable password authentication of the default ModelBackend."""
        if getattr(settings, "HELUSERS_PASSWORD_LOGIN_DISABLED", False):
            return None

        return super().authenticate(request, username, password, **kwargs)
