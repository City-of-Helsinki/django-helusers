from django.conf import settings
from django.core.signals import setting_changed
from django.dispatch import receiver

_defaults = dict(
    AUDIENCE=None,
    API_SCOPE_PREFIX=None,
    REQUIRE_API_SCOPE_FOR_AUTHENTICATION=False,
    API_AUTHORIZATION_FIELD="https://api.hel.fi/auth",
    ISSUER="https://tunnistamo.hel.fi",
    AUTH_SCHEME="Bearer",
    USER_RESOLVER="helusers.oidc.resolve_user",
    OIDC_CONFIG_EXPIRATION_TIME=24 * 60 * 60,
)

_import_strings = [
    "USER_RESOLVER",
]


def _compile_settings():
    class Settings:
        def __init__(self):
            self._load()

        def __getattr__(self, name):
            from django.utils.module_loading import import_string

            try:
                attr = self._settings[name]

                if name in _import_strings and isinstance(attr, str):
                    attr = import_string(attr)
                    self._settings[name] = attr

                return attr
            except KeyError:
                raise AttributeError("Setting '{}' not found".format(name))

        def _load(self):
            self._settings = _defaults.copy()

            user_settings = getattr(settings, "OIDC_API_TOKEN_AUTH", None)
            self._settings.update(user_settings)

    return Settings()


api_token_auth_settings = _compile_settings()


@receiver(setting_changed)
def _reload_settings(setting, **kwargs):
    if setting == "OIDC_API_TOKEN_AUTH":
        api_token_auth_settings._load()
