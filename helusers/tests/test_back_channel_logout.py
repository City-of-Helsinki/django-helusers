import pytest
from django.test import Client

from .conftest import encoded_jwt_factory, ISSUER1


_NOT_PROVIDED = object()


def build_logout_token(**kwargs):
    if "iss" not in kwargs:
        kwargs["iss"] = ISSUER1

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


def test_require_logout_token_parameter():
    response = execute_back_channel_logout(overwrite_token=None)
    assert response.status_code == 400


def test_handle_undecodable_logout_token():
    response = execute_back_channel_logout(overwrite_token="invalid_token")
    assert response.status_code == 400


def test_issuer_is_required():
    response = execute_back_channel_logout(iss=None)
    assert response.status_code == 400


def test_issuer_not_found_from_settings_is_not_accepted():
    response = execute_back_channel_logout(iss="unknown_issuer")
    assert response.status_code == 400
