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
USER_UUID = uuid.UUID("b7a35517-eb1f-46c9-88bf-3206fb659c3c")


def update_oidc_settings(settings, updates):
    oidc_settings = settings.OIDC_API_TOKEN_AUTH.copy()
    oidc_settings.update(updates)
    settings.OIDC_API_TOKEN_AUTH = oidc_settings


def public_key_provider(issuer):
    return [rsa_key.public_key_jwk]


def do_authentication(
    issuer=ISSUER,
    audience=AUDIENCE,
    signing_key=rsa_key,
    expiration=-1,
    not_before=None,
    key_provider=public_key_provider,
    auth_scheme="Bearer",
    **kwargs,
):
    sut = RequestJWTAuthentication(key_provider=key_provider)

    jwt_data = {
        "sub": str(USER_UUID),
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

    for k, v in kwargs.items():
        jwt_data[k] = v

    encoded_jwt = jwt.encode(
        jwt_data, key=signing_key.private_key_pem, algorithm=signing_key.jose_algorithm
    )

    rf = RequestFactory()
    request = rf.get("/path", HTTP_AUTHORIZATION=f"{auth_scheme} {encoded_jwt}")

    return sut.authenticate(request)


def authentication_passes(**kwargs):
    auth = do_authentication(**kwargs)
    assert auth.user.uuid == USER_UUID


def authentication_does_not_pass(**kwargs):
    with pytest.raises(AuthenticationError):
        do_authentication(**kwargs)


def authentication_is_skipped(**kwargs):
    assert do_authentication(**kwargs) is None


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


@pytest.mark.django_db
def test_audience_in_token_can_be_a_list():
    authentication_passes(audience=["some_audience", AUDIENCE, "another_audience"])

    authentication_does_not_pass(audience=["some_audience", "another_audience"])


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


@pytest.mark.django_db
def test_default_key_provider_fetches_keys_from_issuer_server(mock_responses):
    CONFIG_URL = f"{ISSUER}/.well-known/openid-configuration"
    JWKS_URL = f"{ISSUER}/jwks"

    CONFIGURATION = {
        "jwks_uri": JWKS_URL,
    }

    KEYS = {"keys": [rsa_key.public_key_jwk]}

    mock_responses.add(method="GET", url=CONFIG_URL, json=CONFIGURATION)
    mock_responses.add(method="GET", url=JWKS_URL, json=KEYS)

    authentication_passes(key_provider=None)


class TestApiScopeChecking:
    @staticmethod
    def enable_api_scope_checking(settings):
        update_oidc_settings(
            settings,
            {
                "REQUIRE_API_SCOPE_FOR_AUTHENTICATION": True,
                "API_AUTHORIZATION_FIELD": "authorization",
                "API_SCOPE_PREFIX": "api_scope",
            },
        )

    @pytest.mark.django_db
    def test_if_required_api_scope_is_found_as_is_then_authentication_passes(
        self, settings
    ):
        self.enable_api_scope_checking(settings)
        authentication_passes(authorization=["api_scope", "another_api_scope"])

    @pytest.mark.django_db
    def test_if_required_api_scope_is_found_as_a_prefix_then_authentication_passes(
        self, settings
    ):
        self.enable_api_scope_checking(settings)
        authentication_passes(authorization=["api_scope.read"])

    def test_if_required_api_authorization_field_is_missing_then_authentication_fails(
        self, settings
    ):
        self.enable_api_scope_checking(settings)
        authentication_does_not_pass()

    def test_if_required_api_scope_is_not_found_then_authentication_fails(
        self, settings
    ):
        self.enable_api_scope_checking(settings)
        authentication_does_not_pass(authorization=["another_api_scope"])


def test_if_authorization_header_is_missing_returns_none(rf):
    request = rf.get("/path")
    assert RequestJWTAuthentication().authenticate(request) is None


@pytest.mark.parametrize(
    "auth", ["TooShort", "Unknown scheme", "Bearer not_a_jwt", "Too many parts"]
)
def test_if_authorization_header_does_not_contain_a_jwt_returns_none(rf, auth):
    request = rf.get("/path", HTTP_AUTHORIZATION=auth)
    assert RequestJWTAuthentication().authenticate(request) is None


@pytest.mark.django_db
def test_bearer_authentication_scheme_is_accepted():
    authentication_passes(auth_scheme="Bearer")


def test_other_than_bearer_authentication_scheme_makes_authentication_skip():
    authentication_is_skipped(auth_scheme="Auth")
