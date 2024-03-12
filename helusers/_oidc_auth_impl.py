import logging

from cachetools.func import ttl_cache
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _
from jose import JWTError
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .authz import UserAuthorization
from .jwt import JWT, ValidationError
from .settings import api_token_auth_settings
from .user_utils import get_or_create_user

logger = logging.getLogger(__name__)


class ApiTokenAuthentication(BaseAuthentication):
    www_authenticate_realm = "api"

    def __init__(self, settings=None, **kwargs):
        self.settings = settings or api_token_auth_settings
        super(ApiTokenAuthentication, self).__init__(**kwargs)

    @property
    def auth_scheme(self):
        return self.settings.AUTH_SCHEME or "Bearer"

    @ttl_cache(ttl=api_token_auth_settings.OIDC_CONFIG_EXPIRATION_TIME)
    def get_oidc_config(self, issuer):
        from helusers.oidc import OIDCConfig

        return OIDCConfig(issuer)

    def authenticate(self, request):
        jwt_value = self.get_jwt_value(request)
        if jwt_value is None:
            return None

        try:
            payload = self.decode_jwt(jwt_value)
        except JWTError:
            return None

        logger.debug("Token payload decoded as: {}".format(payload))

        user_resolver = self.settings.USER_RESOLVER  # Default: resolve_user
        try:
            user = user_resolver(request, payload)
        except ValueError as e:
            raise AuthenticationFailed(str(e)) from e
        auth = UserAuthorization(user, payload, self.settings)

        return user, auth

    def decode_jwt(self, jwt_value):
        jwt = JWT(jwt_value, settings=self.settings)

        try:
            jwt.validate_issuer()
        except ValidationError as e:
            raise AuthenticationFailed(str(e)) from e

        keys = self.get_oidc_config(jwt.issuer).keys()
        try:
            jwt.validate(keys, self.settings.AUDIENCE)
            jwt.validate_api_scope()
            jwt.validate_session()
            self.validate_claims(jwt.claims)
        except ValidationError as e:
            raise AuthenticationFailed(str(e)) from e
        except Exception:
            raise AuthenticationFailed("JWT verification failed.")

        return jwt.claims

    def get_jwt_value(self, request):
        auth = get_authorization_header(request).split()

        logger.debug("Authorization header: {}".format(auth))

        if not auth or smart_str(auth[0]).lower() != self.auth_scheme.lower():
            return None

        if len(auth) == 1:
            raise AuthenticationFailed(
                _("Invalid Authorization header. No credentials provided")
            )
        elif len(auth) > 2:
            raise AuthenticationFailed(
                _(
                    "Invalid Authorization header. "
                    "Credentials string should not contain spaces."
                )
            )

        return auth[1]

    def validate_claims(self, id_token):
        """Not in use. Only for backwards compatibility"""

    def authenticate_header(self, request):
        return '{auth_scheme} realm="{realm}"'.format(
            auth_scheme=self.auth_scheme, realm=self.www_authenticate_realm
        )


def resolve_user(request, payload):
    return get_or_create_user(payload, oidc=True)
