from django.conf import settings
from rest_framework.settings import APISettings


_user_settings = getattr(settings, 'HELSINKI_ID_TOKEN_AUTH', None)

_defaults = dict(
    # Accepted audience, the ID token must have this in its aud field
    AUDIENCE=None,

    # URL of the OpenID Provider
    ISSUER='https://oma.hel.fi',

    # Auth scheme used in the Authorization header
    AUTH_SCHEME='Bearer',

    # Function for resolving users
    USER_RESOLVER='helusers.oidc.resolve_user',
)

_import_strings = [
    'USER_RESOLVER',
]

api_settings = APISettings(_user_settings, _defaults, _import_strings)
