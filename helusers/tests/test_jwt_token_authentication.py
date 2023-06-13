import uuid

import pytest
from django.test.client import RequestFactory
from rest_framework.exceptions import AuthenticationFailed

from helusers.oidc import AuthenticationError, RequestJWTAuthentication

from .conftest import AUDIENCE, encoded_jwt_factory, ISSUER1, unix_timestamp_now
from .keys import rsa_key, rsa_key2
from .test_back_channel_logout import execute_back_channel_logout
from .._oidc_auth_impl import ApiTokenAuthentication

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
    issued_at=None,
    sut=None,
    **kwargs,
):
    if sut is None:
        sut = RequestJWTAuthentication()

    now = unix_timestamp_now()
    if issued_at is None:
        issued_at = now

    if expiration == -1:
        expiration = now + 2

    encoded_jwt = encoded_jwt_factory(
        iss=issuer,
        sub=str(USER_UUID),
        aud=audience,
        iat=issued_at,
        exp=expiration,
        nbf=not_before,
        signing_key=signing_key,
        **kwargs,
    )

    rf = RequestFactory()
    request = rf.get("/path", HTTP_AUTHORIZATION=f"{auth_scheme} {encoded_jwt}")

    result = sut.authenticate(request)
    if isinstance(sut, ApiTokenAuthentication) and isinstance(result, tuple):
        # Only return UserAuthorization when authenticating with ApiTokenAuthentication
        return result[1]
    else:
        return result


@pytest.fixture(params=[ApiTokenAuthentication, RequestJWTAuthentication])
def sut(request):
    return request.param()


def authentication_passes(**kwargs):
    auth = do_authentication(**kwargs)
    assert auth.user.uuid == USER_UUID


def authentication_does_not_pass(**kwargs):
    exception_class = AuthenticationError
    if isinstance(kwargs.get("sut"), ApiTokenAuthentication):
        exception_class = AuthenticationFailed

    with pytest.raises(exception_class):
        do_authentication(**kwargs)


def authentication_is_skipped(**kwargs):
    assert do_authentication(**kwargs) is None


@pytest.mark.django_db
def test_valid_jwt_is_accepted(sut):
    authentication_passes(sut=sut)


def test_invalid_signature_is_not_accepted(sut):
    authentication_does_not_pass(sut=sut, signing_key=rsa_key2)


def test_issuer_is_required(sut):
    authentication_does_not_pass(sut=sut, issuer=None)


@pytest.mark.django_db
def test_any_issuer_from_settings_is_accepted(sut, all_auth_servers):
    if isinstance(sut, ApiTokenAuthentication):
        pytest.skip("ApiTokenAuthentication doesn't support multiple issuers yet")

    signing_key = all_auth_servers.key
    authentication_passes(sut=sut, issuer=all_auth_servers.issuer, signing_key=signing_key)


def test_issuer_not_found_from_settings_is_not_accepted(sut):
    authentication_does_not_pass(sut=sut, issuer="unknown_issuer")


def test_audience_is_required(sut):
    authentication_does_not_pass(sut=sut, audience=None)


@pytest.mark.django_db
def test_audience_from_settings_is_accepted(sut):
    authentication_passes(sut=sut, audience=AUDIENCE)


@pytest.mark.django_db
def test_audience_in_token_can_be_a_list(sut):
    authentication_passes(sut=sut, audience=["some_audience", AUDIENCE, "another_audience"])

    authentication_does_not_pass(sut=sut, audience=["some_audience", "another_audience"])


def test_audience_not_found_from_settings_is_not_accepted(sut):
    authentication_does_not_pass(sut=sut, audience="unknown_audience")


@pytest.mark.django_db
def test_audiences_setting_can_be_multi_valued(sut, settings):
    audiences = ["test_audience1", "test_audience2"]

    update_oidc_settings(
        settings,
        {
            "AUDIENCE": audiences,
        },
    )

    for audience in audiences:
        authentication_passes(sut=sut, audience=audience)
        authentication_passes(sut=sut, audience=["some_audience", audience, "another_audience"])

    authentication_does_not_pass(sut=sut, audience="unknown_audience")


def test_expiration_is_required(sut):
    authentication_does_not_pass(sut=sut, expiration=None)


@pytest.mark.django_db
def test_expiration_in_the_future_is_accepted(sut, unix_timestamp_now):
    authentication_passes(sut=sut, expiration=unix_timestamp_now + 2)


def test_expiration_in_the_past_is_not_accepted(sut, unix_timestamp_now):
    authentication_does_not_pass(sut=sut, expiration=unix_timestamp_now - 1)


@pytest.mark.django_db
def test_not_before_is_not_required(sut):
    authentication_passes(sut=sut, not_before=None)


def test_not_before_in_the_future_is_not_accepted(sut, unix_timestamp_now):
    authentication_does_not_pass(sut=sut, not_before=unix_timestamp_now + 2)


@pytest.mark.django_db
def test_not_before_in_the_past_is_accepted(sut, unix_timestamp_now):
    authentication_passes(sut=sut, not_before=unix_timestamp_now - 1)


@pytest.mark.django_db
class TestApiScopeChecking:
    @pytest.fixture(autouse=True)
    def enable_api_scope_checking(self, settings):
        update_oidc_settings(
            settings,
            {
                "REQUIRE_API_SCOPE_FOR_AUTHENTICATION": True,
                "API_AUTHORIZATION_FIELD": "https://example.com",
                "API_SCOPE_PREFIX": "api_scope",
            },
        )

    def test_if_required_api_scope_is_found_as_is_then_authentication_passes(self, sut):
        authentication_passes(
            sut=sut,
            **{"https://example.com": ["api_scope", "another_api_scope"]}
        )

    def test_if_required_api_scope_is_found_as_a_prefix_then_authentication_passes(
        self, sut
    ):
        authentication_passes(sut=sut, **{"https://example.com": ["api_scope.read"]})

    def test_if_required_api_authorization_field_is_missing_then_authentication_fails(
        self, sut
    ):
        authentication_does_not_pass(sut=sut)

    def test_if_required_api_scope_is_not_found_then_authentication_fails(self, sut):
        authentication_does_not_pass(
            sut=sut,
            **{"https://example.com": ["another_api_scope"]}
        )


def test_if_authorization_header_is_missing_returns_none(rf, sut):
    request = rf.get("/path")
    assert sut.authenticate(request) is None


@pytest.mark.parametrize(
    "auth", ["TooShort", "Unknown scheme", "Too many parts"]
)
def test_if_authorization_header_does_not_contain_a_correct_prefix_returns_none(
    rf, sut, auth
):
    request = rf.get("/path", HTTP_AUTHORIZATION=auth)
    assert sut.authenticate(request) is None


def test_if_authorization_header_does_not_contain_a_valid_jwt_returns_none(rf):
    request = rf.get("/path", HTTP_AUTHORIZATION="Bearer not_a_jwt")
    assert RequestJWTAuthentication().authenticate(request) is None


def test_failure_if_authorization_header_does_not_contain_a_valid_jwt(rf):
    request = rf.get("/path", HTTP_AUTHORIZATION="Bearer not_a_jwt")
    with pytest.raises(AuthenticationFailed):
        ApiTokenAuthentication().authenticate(request)


@pytest.mark.django_db
@pytest.mark.parametrize("scheme", ["Bearer", "bearer", "BEARER", "BeArEr"])
def test_bearer_authentication_scheme_is_accepted(sut, scheme):
    authentication_passes(sut=sut, auth_scheme=scheme)


def test_other_than_bearer_authentication_scheme_makes_authentication_skip(sut):
    authentication_is_skipped(sut=sut, auth_scheme="Auth")


@pytest.mark.django_db
def test_token_belonging_to_a_logged_out_session_is_not_accepted(sut):
    if isinstance(sut, ApiTokenAuthentication):
        pytest.skip("ApiTokenAuthentication doesn't check for terminated sessions")

    iss = ISSUER1
    sub = str(USER_UUID)
    sid = "logged_out_session"

    execute_back_channel_logout(iss=iss, sub=sub, sid=sid)

    authentication_does_not_pass(sut=sut, issuer=iss, sid=sid)
    authentication_passes(sut=sut, issuer=iss, sid="other_session")
