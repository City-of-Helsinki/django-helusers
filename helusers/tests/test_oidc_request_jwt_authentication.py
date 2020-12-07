import uuid

import pytest
from django.test.client import RequestFactory
from jose import jwt

from helusers.oidc import AuthenticationError, RequestJWTAuthentication
from helusers.settings import api_token_auth_settings

from .conftest import unix_timestamp_now
from .keys import rsa_key, rsa_key2

ISSUER = api_token_auth_settings.ISSUER[0]
AUDIENCE = api_token_auth_settings.AUDIENCE


def public_key_provider(issuer):
    return [rsa_key.public_key_jwk]


def do_authentication(
    issuer=ISSUER,
    audience=AUDIENCE,
    signing_key=rsa_key,
    expiration=-1,
    not_before=None,
):
    sut = RequestJWTAuthentication(key_provider=public_key_provider)

    user_uuid = uuid.UUID("b7a35517-eb1f-46c9-88bf-3206fb659c3c")
    jwt_data = {
        "sub": str(user_uuid),
    }

    if issuer:
        jwt_data["iss"] = issuer

    if audience:
        jwt_data["aud"] = audience

    if expiration:
        expiration = unix_timestamp_now() + 2 if expiration == -1 else expiration
        jwt_data["exp"] = expiration

    if not_before:
        jwt_data["nbf"] = not_before

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


def test_audience_is_required():
    authentication_does_not_pass(audience=None)


@pytest.mark.django_db
def test_audience_from_settings_is_accepted():
    authentication_passes(audience=AUDIENCE)


def test_audience_not_found_from_settings_is_not_accepted():
    authentication_does_not_pass(audience="unknown_audience")


def test_expiration_is_required():
    authentication_does_not_pass(expiration=None)


@pytest.mark.django_db
def test_expiration_in_the_future_is_accepted(unix_timestamp_now):
    authentication_passes(expiration=unix_timestamp_now + 2)


def test_expiration_in_the_past_is_not_accepted(unix_timestamp_now):
    authentication_does_not_pass(expiration=unix_timestamp_now - 1)


@pytest.mark.django_db
def test_not_before_is_not_required():
    authentication_passes(not_before=None)


def test_not_before_in_the_future_is_not_accepted(unix_timestamp_now):
    authentication_does_not_pass(not_before=unix_timestamp_now + 2)


@pytest.mark.django_db
def test_not_before_in_the_past_is_accepted(unix_timestamp_now):
    authentication_passes(not_before=unix_timestamp_now - 1)
