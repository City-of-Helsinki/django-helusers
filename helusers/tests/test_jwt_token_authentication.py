import uuid

import pytest
from django.test.client import RequestFactory

from helusers.oidc import AuthenticationError, RequestJWTAuthentication

from .conftest import AUDIENCE, encoded_jwt_factory, ISSUER1, unix_timestamp_now
from .keys import rsa_key, rsa_key2
from .test_back_channel_logout import execute_back_channel_logout

USER_UUID = uuid.UUID("b7a35517-eb1f-46c9-88bf-3206fb659c3c")


@pytest.fixture(autouse=True)
def auto_auth_server(auth_server):
    return auth_server


def update_oidc_settings(settings, updates):
    oidc_settings = settings.OIDC_API_TOKEN_AUTH.copy()
    oidc_settings.update(updates)
    settings.OIDC_API_TOKEN_AUTH = oidc_settings


def do_authentication(
    issuer=ISSUER1,
    audience=AUDIENCE,
    signing_key=rsa_key,
    expiration=-1,
    not_before=None,
    auth_scheme="Bearer",
    sut=None,
    **kwargs,
):
    if sut is None:
        sut = RequestJWTAuthentication()

    if expiration == -1:
        expiration = unix_timestamp_now() + 2

    encoded_jwt = encoded_jwt_factory(
        iss=issuer,
        sub=str(USER_UUID),
        aud=audience,
        exp=expiration,
        nbf=not_before,
        signing_key=signing_key,
        **kwargs,
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


@pytest.mark.django_db
def test_any_issuer_from_settings_is_accepted(all_auth_servers):
    signing_key = all_auth_servers.key
    authentication_passes(issuer=all_auth_servers.issuer, signing_key=signing_key)


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


@pytest.mark.django_db
def test_audiences_setting_can_be_multi_valued(settings):
    audiences = ["test_audience1", "test_audience2"]

    update_oidc_settings(
        settings,
        {
            "AUDIENCE": audiences,
        },
    )

    for audience in audiences:
        authentication_passes(audience=audience)
        authentication_passes(audience=["some_audience", audience, "another_audience"])

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
@pytest.mark.parametrize("scheme", ["Bearer", "bearer", "BEARER", "BeArEr"])
def test_bearer_authentication_scheme_is_accepted(scheme):
    authentication_passes(auth_scheme=scheme)


def test_other_than_bearer_authentication_scheme_makes_authentication_skip():
    authentication_is_skipped(auth_scheme="Auth")


@pytest.mark.django_db
def test_token_belonging_to_a_logged_out_session_is_not_accepted():
    iss = ISSUER1
    sub = str(USER_UUID)
    sid = "logged_out_session"

    execute_back_channel_logout(iss=iss, sub=sub, sid=sid)

    authentication_does_not_pass(issuer=iss, sid=sid)
    authentication_passes(issuer=iss, sid="other_session")
