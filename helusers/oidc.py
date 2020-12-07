try:
    from ._oidc_auth_impl import ApiTokenAuthentication, resolve_user
except ImportError:
    pass


import requests
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import cached_property

from .authz import UserAuthorization
from .jwt import JWT
from .settings import api_token_auth_settings
from .user_utils import get_or_create_user


class OIDCConfig:
    def __init__(self, issuer):
        self._issuer = issuer

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
        """Looks for a JWT from the request's "Authorization" header and verifies it.
        If verification passes, takes a user's id from the JWT's "sub" claim.
        Creates a User if it doesn't already exist. On success returns the User
        and a UserAuthorization object as a (User, UserAuthorization) tuple.
        Raises an AuthenticationError on authentication failure."""
        auth = request.headers["Authorization"].split()
        jwt_value = auth[1]

        jwt = JWT(jwt_value)

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

        claims = jwt.claims
        user = get_or_create_user(claims, oidc=True)
        auth = UserAuthorization(user, claims)

        return (user, auth)
