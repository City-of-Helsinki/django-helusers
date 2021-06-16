import time

from helusers.oidc import OIDCConfig
from helusers.settings import api_token_auth_settings


def test_keys_are_returned_and_cached_with_an_expiration_time(
    auth_server, stub_responses
):
    ttl = api_token_auth_settings.OIDC_CONFIG_EXPIRATION_TIME

    config = OIDCConfig(auth_server.issuer)

    assert config.keys() == auth_server.keys_response
    time.sleep(ttl - 1)
    assert config.keys() == auth_server.keys_response

    assert stub_responses.assert_call_count(auth_server.config_url, 1) is True
    assert stub_responses.assert_call_count(auth_server.jwks_url, 1) is True

    time.sleep(1)
    assert config.keys() == auth_server.keys_response

    assert stub_responses.assert_call_count(auth_server.config_url, 2) is True
    assert stub_responses.assert_call_count(auth_server.jwks_url, 2) is True
