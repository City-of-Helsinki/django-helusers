import urllib.parse as urlparse

from social_core.backends.open_id_connect import OpenIdConnectAuth
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch


class TunnistamoOIDCAuth(OpenIdConnectAuth):
    name = 'tunnistamo'
    OIDC_ENDPOINT = 'https://api.hel.fi/sso/openid'
    END_SESSION_URL = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow OIDC endpoint to be overridden through local settings
        self.OIDC_ENDPOINT = self.setting('OIDC_ENDPOINT', self.OIDC_ENDPOINT)

    def get_end_session_url(self, request, id_token):
        url = self.END_SESSION_URL or \
            self.oidc_config().get('end_session_endpoint')

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
