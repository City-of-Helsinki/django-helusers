import json
import uuid

import pytest

from helusers.oidc import ApiTokenAuthentication

from .conftest import encoded_jwt_factory, ISSUER1
from .keys import rsa_key


class _TestableApiTokenAuthentication(ApiTokenAuthentication):
    @property
    def oidc_config(self):
        return {
            "issuer": ISSUER1,
        }

    def jwks_data(self):
        return json.dumps({"keys": [rsa_key.public_key_jwk]})


@pytest.mark.django_db
def test_valid_jwt_is_accepted(rf, unix_timestamp_now):
    sut = _TestableApiTokenAuthentication()

    user_uuid = uuid.UUID("b7a35517-eb1f-46c9-88bf-3206fb659c3c")

    encoded_jwt = encoded_jwt_factory(
        iss=ISSUER1,
        aud="test_audience",
        iat=unix_timestamp_now - 10,
        exp=unix_timestamp_now + 1000,
        sub=str(user_uuid),
    )

    request = rf.get("/path", HTTP_AUTHORIZATION=f"Bearer {encoded_jwt}")

    (user, auth) = sut.authenticate(request)

    assert user.uuid == user_uuid
    assert auth.user == user
