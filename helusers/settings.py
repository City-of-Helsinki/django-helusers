from django.conf import settings
from rest_framework.settings import APISettings


_user_settings = getattr(settings, 'HELSINKI_ID_TOKEN_AUTH', None)

_defaults = dict(
    # Accepted audience, the ID token must have this in its aud field
    AUDIENCE=None,

    # API scope prefix for permission checks
    API_SCOPE_PREFIX=None,

    # Is API scope required for successful authentication.
    #
    # If this setting is set, then authentication will fail, if the API
    # scopes field doesn't contain the API_SCOPE_PREFIX or any value that
    # starts with API_SCOPE_PREFIX and a dot.
    #
    # E.g. if API_SCOPE_PREFIX='xyz' and this is set to true, then the
    # authentication will fail if the API scopes doesn't contain either
    # 'xyz' or an item that starts with 'xyz.' (like 'xyz.readonly' or
    # 'xyz.view').
    REQUIRE_API_SCOPE_FOR_AUTHENTICATION=False,

    # Field name containing the API scopes authorized by the user
    API_AUTHORIZATION_FIELD='https://api.hel.fi/auth',

    # Field name containing the AD groups of the user
    AD_GROUPS_FIELD='ad_groups', # TODO: Maybe we should use 'https://api.hel.fi/auth/ad-groups' ?

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
