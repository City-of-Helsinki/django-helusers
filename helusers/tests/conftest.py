from datetime import datetime, timezone

import pytest
import responses
from jose import jwt

from helusers.settings import api_token_auth_settings

from .keys import rsa_key, rsa_key2

ISSUER1 = api_token_auth_settings.ISSUER[0]
ISSUER2 = api_token_auth_settings.ISSUER[1]
AUDIENCE = api_token_auth_settings.AUDIENCE


class AuthServer:
    def __init__(self, issuer):
        self.issuer = issuer
        self.config_url = f"{issuer}/.well-known/openid-configuration"
        self.jwks_url = f"{issuer}/jwks"
        self.configuration = {
            "jwks_uri": self.jwks_url,
        }

        ISSUER_KEYS = {
            ISSUER1: rsa_key,
            ISSUER2: rsa_key2,
        }
        self.key = ISSUER_KEYS[issuer]
        self.keys_response = {"keys": [self.key.public_key_jwk]}


@pytest.fixture
def stub_responses():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as stub_resps:
        yield stub_resps


def unix_timestamp_now():
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    return int((datetime.now(tz=timezone.utc) - epoch).total_seconds())


@pytest.fixture(name="unix_timestamp_now")
def unix_timestamp_now_fixture():
    return unix_timestamp_now()


def encoded_jwt_factory(signing_key=rsa_key, **claims):
    jwt_data = {}

    for name, value in claims.items():
        if value is not None:
            jwt_data[name] = value

    return jwt.encode(
        jwt_data, key=signing_key.private_key_pem, algorithm=signing_key.jose_algorithm
    )


def _configure_auth_server(issuer, stub_responses):
    server = AuthServer(issuer)

    stub_responses.add(method="GET", url=server.config_url, json=server.configuration)
    stub_responses.add(method="GET", url=server.jwks_url, json=server.keys_response)

    return server


@pytest.fixture
def auth_server(stub_responses):
    return _configure_auth_server(ISSUER1, stub_responses)


@pytest.fixture(params=[ISSUER1, ISSUER2])
def all_auth_servers(stub_responses, request):
    return _configure_auth_server(request.param, stub_responses)
