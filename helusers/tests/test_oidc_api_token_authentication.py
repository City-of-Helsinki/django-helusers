import uuid

import pytest

from helusers.oidc import ApiTokenAuthentication

from .conftest import encoded_jwt_factory, ISSUER1


@pytest.fixture(autouse=True)
def auto_auth_server(auth_server):
    return auth_server


@pytest.mark.django_db
def test_valid_jwt_is_accepted(rf, unix_timestamp_now):
    sut = ApiTokenAuthentication()

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
