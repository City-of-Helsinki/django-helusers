from helusers.oidc import resolve_user
from helusers.settings import api_token_auth_settings


def test_defaults_exist_for_settings():
    assert api_token_auth_settings.AUTH_SCHEME == "Bearer"


def test_user_settings_overwrite_defaults():
    assert api_token_auth_settings.AUDIENCE == "test_audience"


def test_USER_RESOLVER_setting_is_returned_as_class():
    user_resolver = api_token_auth_settings.USER_RESOLVER
    assert user_resolver == resolve_user
