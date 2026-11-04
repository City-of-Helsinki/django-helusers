from inspect import signature

from social_core.backends.open_id_connect import OpenIdConnectAuth

from helusers.tunnistamo_oidc import TunnistamoOIDCAuth


def test_get_remote_jwks_keys_with_and_without_uri(auth_server, stub_responses):
    assert "alg" not in auth_server.keys_response["keys"][0]

    backend = TunnistamoOIDCAuth()
    call_args = [()]
    if "uri" in signature(OpenIdConnectAuth.get_remote_jwks_keys).parameters:
        call_args.append((auth_server.jwks_url,))

    for args in call_args:
        keys = backend.get_remote_jwks_keys(*args)
        assert [key["alg"] for key in keys] == ["RS256"]

    assert (
        stub_responses.assert_call_count(auth_server.jwks_url, len(call_args)) is True
    )
