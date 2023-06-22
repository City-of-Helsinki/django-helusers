import pytest

from helusers.authz import UserAuthorization
from helusers.tests.test_jwt_token_authentication import update_oidc_settings


@pytest.fixture(params=[
    {
        "authorization_field": "https://example.com",
        "prefix": "api_scope",
    },
    {
        "authorization_field": ["https://example.com"],
        "prefix": ["api_scope"],
    },
    {
        "authorization_field": [
            "https://example.com",
            "authorization.permissions.scopes",
        ],
        "prefix": ["api_scope", "access"],
    },
], ids=["string settings","array_settings_one","array_settings_multiple"])
def tunnistamo_api_scope_settings(request, settings):
    update_oidc_settings(
        settings,
        {
            "REQUIRE_API_SCOPE_FOR_AUTHENTICATION": True,
            "API_AUTHORIZATION_FIELD": request.param["authorization_field"],
            "API_SCOPE_PREFIX": request.param["prefix"],
        },
    )


def tunnistamo_scopes_payload(scopes):
    return {
        "https://example.com": scopes
    }


@pytest.mark.parametrize("api_token_payload,expected", [
    [tunnistamo_scopes_payload([]), False],
    [tunnistamo_scopes_payload(["api_scope"]), False],
    [tunnistamo_scopes_payload(["api_scope.read"]), False],
    [tunnistamo_scopes_payload(["api_scope", "another_api_scope"]), True],
    [tunnistamo_scopes_payload(["api_scope", "another_api_scope", "third"]), True],
    [tunnistamo_scopes_payload(["another_api_scope"]), False],
], ids=str)
def test_has_api_scopes_tunnistamo(
    tunnistamo_api_scope_settings, api_token_payload, expected
):
    auth = UserAuthorization(user=None, api_token_payload=api_token_payload)

    assert auth.has_api_scopes("api_scope", "another_api_scope") is expected


@pytest.mark.parametrize("api_token_payload,expected", [
    [tunnistamo_scopes_payload([]), False],
    [tunnistamo_scopes_payload(["api_scope"]), True],
    [tunnistamo_scopes_payload(["api_scope.read"]), True],
    [tunnistamo_scopes_payload(["api_scope", "another_api_scope"]), True],
    [tunnistamo_scopes_payload(["another_api_scope"]), False],
], ids=str)
def test_has_api_scope_with_prefix_tunnistamo(
    tunnistamo_api_scope_settings, api_token_payload, expected
):
    auth = UserAuthorization(user=None, api_token_payload=api_token_payload)

    assert auth.has_api_scope_with_prefix("api_scope") is expected


@pytest.fixture(params=[
    {
        "authorization_field": "authorization.permissions.scopes",
        "prefix": "access",
    },
    {
        "authorization_field": ["authorization.permissions.scopes"],
        "prefix": ["access"],
    },
    {
        "authorization_field": [
            "https://example.com",
            "authorization.permissions.scopes",
        ],
        "prefix": ["api_scope", "access"],
    },
], ids=["string settings","array_settings_one","array_settings_multiple"])
def keycloak_api_scope_settings(request, settings):
    update_oidc_settings(
        settings,
        {
            "REQUIRE_API_SCOPE_FOR_AUTHENTICATION": True,
            "API_AUTHORIZATION_FIELD": request.param["authorization_field"],
            "API_SCOPE_PREFIX": request.param["prefix"],
        },
    )


def keycloak_scopes_payload(scopes):
    return {
        "authorization": {
            "permissions": [
                {"scopes": [scope]} for scope in scopes
            ]
        }
    }


@pytest.mark.parametrize("api_token_payload,expected", [
    [keycloak_scopes_payload([]), False],
    [keycloak_scopes_payload(["access"]), False],
    [keycloak_scopes_payload(["access.read"]), False],
    [keycloak_scopes_payload(["access", "second"]), True],
    [keycloak_scopes_payload(["access", "second", "third"]), True],
    [keycloak_scopes_payload(["second"]), False],
], ids=str)
def test_has_api_scopes_keycloak(
    keycloak_api_scope_settings, api_token_payload, expected
):
    auth = UserAuthorization(user=None, api_token_payload=api_token_payload)

    assert auth.has_api_scopes("access", "second") is expected


@pytest.mark.parametrize("api_token_payload,expected", [
    [keycloak_scopes_payload([]), False],
    [keycloak_scopes_payload(["access"]), True],
    [keycloak_scopes_payload(["access", "second"]), True],
    [keycloak_scopes_payload(["second"]), False],
], ids=str)
def test_has_api_scope_with_prefix_keycloak(
    keycloak_api_scope_settings, api_token_payload, expected
):
    auth = UserAuthorization(user=None, api_token_payload=api_token_payload)

    assert auth.has_api_scope_with_prefix("access") is expected
