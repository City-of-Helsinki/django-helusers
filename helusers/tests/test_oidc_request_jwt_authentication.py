import uuid

import pytest
from jose import jwt

from helusers.oidc import RequestJWTAuthentication

from .keys import rsa_key


@pytest.mark.django_db
def test_valid_jwt_is_accepted(rf):
    sut = RequestJWTAuthentication()

    user_uuid = uuid.UUID("b7a35517-eb1f-46c9-88bf-3206fb659c3c")
    jwt_data = {
        "sub": str(user_uuid),
    }

    encoded_jwt = jwt.encode(
        jwt_data, key=rsa_key.private_key_pem, algorithm=rsa_key.jose_algorithm
    )

    request = rf.get("/path", HTTP_AUTHORIZATION=f"Bearer {encoded_jwt}")

    (user, auth) = sut.authenticate(request)

    assert user.uuid == user_uuid
    assert auth.user == user
