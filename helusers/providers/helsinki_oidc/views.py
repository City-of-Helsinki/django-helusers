import requests
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)

from .provider import HelsinkiOIDCProvider


class HelsinkiOIDCOAuth2Adapter(OAuth2Adapter):
    provider_id = HelsinkiOIDCProvider.id
    access_token_url = "https://api.hel.fi/sso/openid/token/"
    authorize_url = "https://api.hel.fi/sso/openid/authorize/"
    profile_url = "https://api.hel.fi/sso/openid/userinfo/"

    def complete_login(self, request, app, token, **kwargs):
        headers = {"Authorization": "Bearer {0}".format(token.token)}
        resp = requests.get(self.profile_url, headers=headers)
        assert resp.status_code == 200
        extra_data = resp.json()
        return self.get_provider().sociallogin_from_response(request, extra_data)


oauth2_login = OAuth2LoginView.adapter_view(HelsinkiOIDCOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(HelsinkiOIDCOAuth2Adapter)
