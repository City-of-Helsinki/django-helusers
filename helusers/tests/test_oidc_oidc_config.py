from helusers.oidc import OIDCConfig

ISSUER = "https://test_issuer"
CONFIG_URL = f"{ISSUER}/.well-known/openid-configuration"
JWKS_URL = f"{ISSUER}/jwks"

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


def test_keys_are_returned(mock_responses):
    mock_responses.add(method="GET", url=CONFIG_URL, json=CONFIGURATION)
    mock_responses.add(method="GET", url=JWKS_URL, json=KEYS)

    config = OIDCConfig(ISSUER)

    assert config.keys() == KEYS
