import logging
import urllib.parse as urlparse

from social_core.backends.open_id_connect import OpenIdConnectAuth
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

logger = logging.getLogger(__name__)


class TunnistamoOIDCAuth(OpenIdConnectAuth):
    name = 'tunnistamo'
    OIDC_ENDPOINT = 'https://api.hel.fi/sso/openid'
    END_SESSION_URL = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow OIDC endpoint to be overridden through local settings
        self.OIDC_ENDPOINT = self.setting('OIDC_ENDPOINT', self.OIDC_ENDPOINT)

    # Workaround for the cases where jwks-endpoint does not specify
    # alg for keys. Default to RS256 per:
    # https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation
    def get_remote_jwks_keys(self):
        keys = super().get_remote_jwks_keys()
        for key in keys:
            if 'alg' not in key:
                key['alg'] = 'RS256'

        return keys 

    # Override for logging
    def request_access_token(self, *args, **kwargs):
        response = super().request_access_token(*args, **kwargs)
        logger.debug(f"Token response: {response}")

        return response

    def get_end_session_url(self, request, id_token):
        url = self.END_SESSION_URL or \
            self.oidc_config().get('end_session_endpoint')

        params = {}

        # Sadly Azure AD does not like having ID token included
        # in end_session request. Allow configuring the inclusion.
        if self.setting('ID_TOKEN_IN_END_SESSION', True):
            params = dict(id_token_hint=id_token)

        try:
            post_logout_url = reverse('helusers:auth_logout_complete')
        except NoReverseMatch:
            post_logout_url = None
        if post_logout_url:
            params['post_logout_redirect_uri'] = request.build_absolute_uri(post_logout_url)

        try:
            # Add the params to the end_session URL, which might have query params already
            url_parts = list(urlparse.urlparse(url))
            query = dict(urlparse.parse_qsl(url_parts[4]))
            query.update(params)
            url_parts[4] = urlparse.urlencode(query)
            end_session_url = urlparse.urlunparse(url_parts)
        except Exception:
            end_session_url = None

        return end_session_url
