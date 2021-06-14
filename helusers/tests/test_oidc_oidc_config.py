import time

from helusers.oidc import OIDCConfig
from helusers.settings import api_token_auth_settings

from .conftest import ISSUER1

CONFIG_URL = f"{ISSUER1}/.well-known/openid-configuration"
JWKS_URL = f"{ISSUER1}/jwks"

# This isn't a full OIDC configuration object. It contains only parts relevant for the tests.
CONFIGURATION = {
    "jwks_uri": JWKS_URL,
}

# The key data in this object isn't valid.
KEYS = {
    "keys": [
        {
            "kty": "RSA",
            "alg": "RS256",
            "use": "sig",
            "kid": "12345",
            "n": "mMg6h8eUyc7G",
            "e": "AQAB",
        }
    ]
}


def test_keys_are_returned_and_cached_with_an_expiration_time(mock_responses):
    ttl = api_token_auth_settings.OIDC_CONFIG_EXPIRATION_TIME

    mock_responses.add(method="GET", url=CONFIG_URL, json=CONFIGURATION)
    mock_responses.add(method="GET", url=JWKS_URL, json=KEYS)

    config = OIDCConfig(ISSUER1)

    assert config.keys() == KEYS
    time.sleep(ttl - 1)
    assert config.keys() == KEYS

    assert mock_responses.assert_call_count(CONFIG_URL, 1) is True
    assert mock_responses.assert_call_count(JWKS_URL, 1) is True

    time.sleep(1)
    assert config.keys() == KEYS

    assert mock_responses.assert_call_count(CONFIG_URL, 2) is True
    assert mock_responses.assert_call_count(JWKS_URL, 2) is True
