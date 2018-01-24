from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns
from .provider import TampereProvider

urlpatterns = default_urlpatterns(TampereProvider)
