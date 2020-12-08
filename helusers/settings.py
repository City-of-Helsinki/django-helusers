from django.conf import settings
from django.core.signals import setting_changed
from django.dispatch import receiver

_defaults = dict(
    # Accepted audience, the API Token must have this in its aud field
    AUDIENCE=None,

    # API scope prefix for permission checks
    API_SCOPE_PREFIX=None,

    # Is API scope required for successful authentication.
    #
    # If this setting is set, then authentication will fail, if the API
    # scopes field doesn't contain the API_SCOPE_PREFIX or any value that
    # starts with API_SCOPE_PREFIX and a dot.
    #
    # E.g. if API_SCOPE_PREFIX='xyz' and this is set to true, then the
    # authentication will fail if the API scopes doesn't contain either
    # 'xyz' or an item that starts with 'xyz.' (like 'xyz.readonly' or
    # 'xyz.view').
    REQUIRE_API_SCOPE_FOR_AUTHENTICATION=False,

    # Field name containing the API scopes authorized by the user
    API_AUTHORIZATION_FIELD='https://api.hel.fi/auth',

    # URL of the OpenID Provider
    ISSUER='https://tunnistamo.hel.fi',

    # Auth scheme used in the Authorization header
    AUTH_SCHEME='Bearer',

    # Function for resolving users
    USER_RESOLVER='helusers.oidc.resolve_user',

    # OIDC config expiration time
    OIDC_CONFIG_EXPIRATION_TIME=24 * 60 * 60
)

_import_strings = [
    'USER_RESOLVER',
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
