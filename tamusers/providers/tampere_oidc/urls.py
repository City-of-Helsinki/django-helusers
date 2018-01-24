from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns
from .provider import TampereOIDCProvider

urlpatterns = default_urlpatterns(TampereOIDCProvider)
