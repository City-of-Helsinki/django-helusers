import uuid

import pytest

from helusers.oidc import ApiTokenAuthentication

from .conftest import ISSUER1, encoded_jwt_factory


@pytest.fixture(autouse=True)
def auto_auth_server(auth_server):
    return auth_server


@pytest.fixture
def user_uuid():
    return uuid.UUID("b7a35517-eb1f-46c9-88bf-3206fb659c3c")


@pytest.fixture
def jwt_data(user_uuid, unix_timestamp_now):
    return dict(
        iss=ISSUER1,
        aud="test_audience",
        iat=unix_timestamp_now - 10,
        exp=unix_timestamp_now + 1000,
        sub=str(user_uuid),
    )


@pytest.mark.parametrize(
    "jwt_data_extra",
    [
        dict(),
        dict(amr="something"),
        dict(amr=["something"]),
    ],
)
@pytest.mark.django_db
def test_valid_jwt_is_accepted(rf, jwt_data, user_uuid, jwt_data_extra):
    sut = ApiTokenAuthentication()

    jwt_data.update(jwt_data_extra)
    encoded_jwt = encoded_jwt_factory(**jwt_data)

    request = rf.get("/path", HTTP_AUTHORIZATION=f"Bearer {encoded_jwt}")

    (user, auth) = sut.authenticate(request)

    assert user.uuid == user_uuid
    assert auth.user == user
