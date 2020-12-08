import json
import time
import uuid

import pytest
from jose import jwt

from helusers.oidc import ApiTokenAuthentication

from .keys import rsa_key

ISSUER = "test_issuer"


class _TestableApiTokenAuthentication(ApiTokenAuthentication):
    @property
    def oidc_config(self):
        return {
            "issuer": ISSUER,
        }

    def jwks_data(self):
        return json.dumps({"keys": [rsa_key.public_key_jwk]})


@pytest.mark.django_db
def test_valid_jwt_is_accepted(rf):
    sut = _TestableApiTokenAuthentication()

    unix_timestamp_now = int(time.time())

    user_uuid = uuid.UUID("b7a35517-eb1f-46c9-88bf-3206fb659c3c")
    jwt_data = {
        "iss": ISSUER,
        "aud": "test_audience",
        "iat": unix_timestamp_now - 10,
        "exp": unix_timestamp_now + 1000,
        "sub": str(user_uuid),
    }

    encoded_jwt = jwt.encode(
        jwt_data, key=rsa_key.private_key_pem, algorithm=rsa_key.jose_algorithm
    )

    request = rf.get("/path", HTTP_AUTHORIZATION=f"Bearer {encoded_jwt}")

    (user, auth) = sut.authenticate(request)

    assert user.uuid == user_uuid
    assert auth.user == user
