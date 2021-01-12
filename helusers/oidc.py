try:
    from ._oidc_auth_impl import ApiTokenAuthentication, resolve_user
except ImportError:
    pass


import requests
from cachetools.func import ttl_cache
from django.core.exceptions import ImproperlyConfigured
from django.core.signals import setting_changed
from django.dispatch import receiver
from django.utils.functional import cached_property

from .authz import UserAuthorization
from .jwt import JWT
from .settings import api_token_auth_settings
from .user_utils import get_or_create_user


class OIDCConfig:
    def __init__(self, issuer):
        self._issuer = issuer

    @ttl_cache(ttl=api_token_auth_settings.OIDC_CONFIG_EXPIRATION_TIME)
    def keys(self):
        config_url = self._issuer + "/.well-known/openid-configuration"
        config = requests.get(config_url).json()

        keys_url = config["jwks_uri"]
        return requests.get(keys_url).json()


def _build_defaults():
    class _Defaults:
        @cached_property
        def audience(self):
            if not api_token_auth_settings.AUDIENCE:
                raise ImproperlyConfigured(
                    "You must set OIDC_API_TOKEN_AUTH['AUDIENCE'] setting to the accepted JWT audience."
                )
            return api_token_auth_settings.AUDIENCE

        @cached_property
        def issuers(self):
            issuers = api_token_auth_settings.ISSUER
            if not issuers:
                raise ImproperlyConfigured(
                    "You must set OIDC_API_TOKEN_AUTH['ISSUER'] setting to one or to a list of accepted JWT issuers."
                )
            if isinstance(issuers, str):
                issuers = [issuers]
            return issuers

        @cached_property
        def configs(self):
            configs = dict()
            for issuer in self.issuers:
                configs[issuer] = OIDCConfig(issuer)
            return configs

        @cached_property
        def key_provider(self):
            confs = self.configs

            def _key_provider(issuer):
                return confs[issuer].keys()

            return _key_provider

    return _Defaults()


_defaults = _build_defaults()


@receiver(setting_changed)
def _reload_settings(setting, **kwargs):
    if setting == "OIDC_API_TOKEN_AUTH":
        global _defaults
        _defaults = _build_defaults()


class AuthenticationError(Exception):
    pass


class RequestJWTAuthentication:
    def __init__(self, key_provider=None):
        """
        key_provider: a callable that provides public keys for an issuer. If omitted,
                      the default is used, which fetches keys from the issuer server
                      using the OIDC standard configuration URL.
        """
        self._key_provider = key_provider or _defaults.key_provider

    def authenticate(self, request):
        """Looks for a JWT from the request's "Authorization" header. If the header
        is not found, or it doesn't contain a JWT, returns None.

        If the header is found and contains a JWT then the JWT gets verified.
        If verification passes, takes a user's id from the JWT's "sub" claim.
        Creates a User if it doesn't already exist. On success returns a
        UserAuthorization object. Raises an AuthenticationError on authentication
        failure."""
        try:
            auth_header = request.headers["Authorization"]
            auth_scheme, jwt_value = auth_header.split()
            if auth_scheme.lower() != "bearer":
                return None
            jwt = JWT(jwt_value)
        except Exception:
            return None

        try:
            issuer = jwt.issuer
        except KeyError:
            raise AuthenticationError('Required "iss" claim is missing.')

        if issuer not in _defaults.issuers:
            raise AuthenticationError("Unknown JWT issuer {}.".format(issuer))

        keys = self._key_provider(issuer)
        try:
            jwt.validate(keys, _defaults.audience)
        except Exception:
            raise AuthenticationError("JWT verification failed.")

        if api_token_auth_settings.REQUIRE_API_SCOPE_FOR_AUTHENTICATION:
            api_scope = api_token_auth_settings.API_SCOPE_PREFIX
            if not jwt.has_api_scope_with_prefix(api_scope):
                raise AuthenticationError(
                    'Not authorized for API scope "{}"'.format(api_scope)
                )

        claims = jwt.claims
        user = get_or_create_user(claims, oidc=True)
        return UserAuthorization(user, claims)
