import uuid

import pytest
from django.test.client import RequestFactory
from jose import jwt

from helusers.oidc import AuthenticationError, RequestJWTAuthentication
from helusers.settings import api_token_auth_settings

from .keys import rsa_key, rsa_key2

ISSUER = api_token_auth_settings.ISSUER[0]


def public_key_provider(issuer):
    return [rsa_key.public_key_jwk]


def do_authentication(issuer=ISSUER, signing_key=rsa_key):
    sut = RequestJWTAuthentication(key_provider=public_key_provider)

    user_uuid = uuid.UUID("b7a35517-eb1f-46c9-88bf-3206fb659c3c")
    jwt_data = {
        "sub": str(user_uuid),
    }

    if issuer:
        jwt_data["iss"] = issuer

    encoded_jwt = jwt.encode(
        jwt_data, key=signing_key.private_key_pem, algorithm=rsa_key.jose_algorithm
    )

    rf = RequestFactory()
    request = rf.get("/path", HTTP_AUTHORIZATION=f"Bearer {encoded_jwt}")

    (user, auth) = sut.authenticate(request)

    assert user.uuid == user_uuid
    assert auth.user == user


def authentication_passes(**kwargs):
    do_authentication(**kwargs)


def authentication_does_not_pass(**kwargs):
    with pytest.raises(AuthenticationError):
        do_authentication(**kwargs)


@pytest.mark.django_db
def test_valid_jwt_is_accepted():
    authentication_passes()


def test_invalid_signature_is_not_accepted():
    authentication_does_not_pass(signing_key=rsa_key2)


def test_issuer_is_required():
    authentication_does_not_pass(issuer=None)


@pytest.mark.parametrize(
    "issuer",
    api_token_auth_settings.ISSUER,
)
@pytest.mark.django_db
def test_any_issuer_from_settings_is_accepted(issuer):
    authentication_passes(issuer=issuer)


def test_issuer_not_found_from_settings_is_not_accepted():
    authentication_does_not_pass(issuer="unknown_issuer")
