from social_core.backends.open_id_connect import OpenIdConnectAuth


class TunnistamoOIDCAuth(OpenIdConnectAuth):
    name = 'tunnistamo'
    OIDC_ENDPOINT = 'https://api.hel.fi/sso/openid'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow OIDC endpoint to be overridden through local settings
        self.OIDC_ENDPOINT = self.setting('OIDC_ENDPOINT', self.OIDC_ENDPOINT)
