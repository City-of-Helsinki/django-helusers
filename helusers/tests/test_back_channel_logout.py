def test_valid_logout_token_is_accepted(client):
    data = "logout_token=token"
    response = client.post(
        "/logout/oidc/backchannel/",
        data=data,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
