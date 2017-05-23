import requests
from django.utils.encoding import smart_text
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from oidc_auth.authentication import JSONWebTokenAuthentication
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .authz import UserAuthorization
from .settings import api_settings
from .user_utils import get_or_create_user


class IdTokenAuthentication(JSONWebTokenAuthentication):
    def __init__(self, settings=None, **kwargs):
        self.settings = settings or api_settings
        super(IdTokenAuthentication, self).__init__(**kwargs)

    @cached_property
    def auth_scheme(self):
        return self.settings.AUTH_SCHEME or 'Bearer'

    @cached_property
    def oidc_config(self):
        url = self.settings.ISSUER + '/.well-known/openid-configuration'
        return requests.get(url).json()

    def authenticate(self, request):
        jwt_value = self.get_jwt_value(request)
        if jwt_value is None:
            return None

        payload = self.decode_jwt(jwt_value)
        self.validate_claims(payload)

        user_resolver = self.settings.USER_RESOLVER  # Default: resolve_user
        user = user_resolver(request, payload)
        auth = UserAuthorization(user, payload, self.settings)

        if self.settings.REQUIRE_API_SCOPE_FOR_AUTHENTICATION:
            api_scope = self.settings.API_SCOPE_PREFIX
            if not auth.has_api_scope_with_prefix(api_scope):
                raise AuthenticationFailed(
                    _("Not authorized for API scope \"{api_scope}\"")
                    .format(api_scope=api_scope))

        return (user, auth)

    def get_jwt_value(self, request):
        auth = get_authorization_header(request).split()

        if not auth or smart_text(auth[0]).lower() != self.auth_scheme.lower():
            return None

        if len(auth) == 1:
            raise AuthenticationFailed(
                _("Invalid Authorization header. No credentials provided"))
        elif len(auth) > 2:
            raise AuthenticationFailed(
                _("Invalid Authorization header. "
                  "Credentials string should not contain spaces."))

        return auth[1]

    def authenticate_header(self, request):
        return '{auth_scheme} realm="{realm}"'.format(
            auth_scheme=self.auth_scheme,
            realm=self.www_authenticate_realm)

    def get_audiences(self, id_token):
        return {self.settings.AUDIENCE}

    def validate_claims(self, id_token):
        return super(IdTokenAuthentication, self).validate_claims(
            self._simplify_id_token_azp_and_aud(id_token))

    def _simplify_id_token_azp_and_aud(self, id_token):
        """
        Simplify ID token by removing azp and unknown audiences.

        If id_token has azp, drf-oidc-auth checks it incorrectly against
        OIDC_AUDIENCES.  This addresses it, until fix in PR #21 is
        merged and released, see:
        https://github.com/ByteInternet/drf-oidc-auth/pull/21
        """
        audiences = self.get_audiences(id_token)
        if audiences and 'azp' in id_token:
            # Take the first known aud and set is as the single aud
            new_aud = [
                aud for aud in _listify(id_token['aud'])
                if aud in audiences
            ][0:1]
            # Return ID token with simplified aud and unset azp
            return dict(id_token, aud=new_aud, azp=None)
        return id_token


def _listify(x):
    return x if isinstance(x, list) else [x]


def resolve_user(request, payload):
    return get_or_create_user(payload)
