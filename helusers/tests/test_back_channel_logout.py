import re

import pytest
from django.test import Client

from .conftest import AUDIENCE, encoded_jwt_factory, ISSUER1, unix_timestamp_now
from .keys import rsa_key2


_NOT_PROVIDED = object()


@pytest.fixture(autouse=True)
def auto_auth_server(auth_server):
    return auth_server


def build_logout_token(**kwargs):
    if "iss" not in kwargs:
        kwargs["iss"] = ISSUER1

    if "aud" not in kwargs:
        kwargs["aud"] = AUDIENCE

    if "iat" not in kwargs:
        kwargs["iat"] = unix_timestamp_now() - 1

    if "jti" not in kwargs:
        kwargs["jti"] = "jwt_id"

    if "sub" not in kwargs:
        kwargs["sub"] = "sub_value"

    if "events" not in kwargs:
        kwargs["events"] = {"http://schemas.openid.net/event/backchannel-logout": {}}

    return encoded_jwt_factory(**kwargs)


def execute_back_channel_logout(
    http_method="post",
    content_type="application/x-www-form-urlencoded",
    overwrite_token=_NOT_PROVIDED,
    **kwargs,
):
    params = {}

    if overwrite_token is not None:
        token = (
            build_logout_token(**kwargs)
            if overwrite_token is _NOT_PROVIDED
            else overwrite_token
        )

        if content_type == "application/x-www-form-urlencoded":
            params["data"] = f"logout_token={token}"
        else:
            params["data"] = {"logout_token": token}

    if content_type:
        params["content_type"] = content_type

    client = Client()
    return getattr(client, http_method)("/logout/oidc/backchannel/", **params)


@pytest.mark.django_db
def test_valid_logout_token_is_accepted(all_auth_servers):
    response = execute_back_channel_logout(
        iss=all_auth_servers.issuer, signing_key=all_auth_servers.key
    )
    assert response.status_code == 200


@pytest.mark.parametrize("http_method", ("get", "head"))
def test_do_not_accept_query_http_methods(http_method):
    response = execute_back_channel_logout(http_method=http_method, content_type=None)
    assert response.status_code == 405


@pytest.mark.parametrize("http_method", ("put", "patch", "delete", "options", "trace"))
def test_accept_only_post_modification_http_method(http_method):
    response = execute_back_channel_logout(http_method=http_method)
    assert response.status_code == 405


def test_require_application_x_www_form_urlencoded_content_type():
    # Test client uses multipart/form-data content type by default for POST requests
    response = execute_back_channel_logout(content_type=None)
    assert response.status_code == 400


@pytest.mark.django_db
def test_include_cache_prevention_response_headers():
    response = execute_back_channel_logout()

    cache_control_header = response.get("Cache-Control", "")
    cache_controls = {
        v.lower() for v in re.split(r"\s*,\s*", cache_control_header) if v
    }
    assert cache_controls == {"no-cache", "no-store"}

    pragma_header = response.get("Pragma", "")
    assert pragma_header == "no-cache"


def test_require_logout_token_parameter():
    response = execute_back_channel_logout(overwrite_token=None)
    assert response.status_code == 400


def test_handle_undecodable_logout_token():
    response = execute_back_channel_logout(overwrite_token="invalid_token")
    assert response.status_code == 400


def test_invalid_signature_is_not_accepted():
    response = execute_back_channel_logout(signing_key=rsa_key2)
    assert response.status_code == 400


def test_issuer_is_required():
    response = execute_back_channel_logout(iss=None)
    assert response.status_code == 400


def test_issuer_not_found_from_settings_is_not_accepted():
    response = execute_back_channel_logout(iss="unknown_issuer")
    assert response.status_code == 400


def test_audience_is_required():
    response = execute_back_channel_logout(aud=None)
    assert response.status_code == 400


@pytest.mark.django_db
def test_audience_in_token_can_be_a_list():
    response = execute_back_channel_logout(
        aud=["some_audience", AUDIENCE, "another_audience"]
    )
    assert response.status_code == 200


def test_audience_not_found_from_settings_is_not_accepted():
    response = execute_back_channel_logout(aud="unknown_audience")
    assert response.status_code == 400


def test_iat_claim_is_required():
    response = execute_back_channel_logout(iat=None)
    assert response.status_code == 400


def test_iat_claim_must_be_a_number():
    response = execute_back_channel_logout(iat="not_number")
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize(
    "sub,sid", [("sub_only", None), (None, "sid_only"), ("both_sub", "and_sid")]
)
def test_accepted_sub_and_sid_claim_combinations(sub, sid):
    response = execute_back_channel_logout(sub=sub, sid=sid)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "sub,sid", [(None, None), ("non_string_sid", 123), (123, "non_string_sub")]
)
def test_rejected_sub_and_sid_claim_combinations(sub, sid):
    response = execute_back_channel_logout(sub=sub, sid=sid)
    assert response.status_code == 400


@pytest.mark.parametrize(
    "value",
    [
        None,
        "not_object",
        {"no_required_member": {}},
        {"http://schemas.openid.net/event/backchannel-logout": "not_object"},
    ],
)
def test_rejected_events_claim_values(value):
    response = execute_back_channel_logout(events=value)
    assert response.status_code == 400


def test_nonce_claim_is_not_allowed():
    response = execute_back_channel_logout(nonce="not allowed")
    assert response.status_code == 400


def test_jti_claim_is_required():
    response = execute_back_channel_logout(jti=None)
    assert response.status_code == 400


@pytest.mark.parametrize("value", [123, {}, []])
def test_jti_claim_must_be_a_string(value):
    response = execute_back_channel_logout(jti=value)
    assert response.status_code == 400


def _callback(**kwargs):
    pass


@pytest.fixture
def callback(settings, mocker):
    callback_mock = mocker.patch(
        "helusers.tests.test_back_channel_logout._callback", autospec=True
    )
    callback_mock.return_value = None
    settings.HELUSERS_BACK_CHANNEL_LOGOUT_CALLBACK = (
        "helusers.tests.test_back_channel_logout._callback"
    )
    return callback_mock


class TestUserProvidedCallback:
    @pytest.mark.django_db
    def test_calls_user_provided_callback_for_valid_token(self, callback):
        execute_back_channel_logout()

        assert callback.call_count == 1

    def test_does_not_call_user_provided_callback_for_invalid_token(self, callback):
        execute_back_channel_logout(iss="unknown_issuer")

        assert callback.call_count == 0
