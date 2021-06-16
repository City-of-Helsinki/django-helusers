from datetime import datetime, timezone

import pytest
import responses
from jose import jwt

from helusers.settings import api_token_auth_settings

from .keys import rsa_key

ISSUER1 = api_token_auth_settings.ISSUER[0]
ISSUER2 = api_token_auth_settings.ISSUER[1]


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
