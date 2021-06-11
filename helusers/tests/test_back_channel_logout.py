from django.test import Client


def execute_back_channel_logout(content_type="application/x-www-form-urlencoded"):
    params = {}

    if content_type == "application/x-www-form-urlencoded":
        params["data"] = "logout_token=token"
    else:
        params["data"] = {"logout_token": "token"}

    if content_type:
        params["content_type"] = content_type

    client = Client()
    return client.post("/logout/oidc/backchannel/", **params)


def test_valid_logout_token_is_accepted():
    response = execute_back_channel_logout()
    assert response.status_code == 200


def test_require_application_x_www_form_urlencoded_content_type():
    # Test client uses multipart/form-data content type by default for POST requests
    response = execute_back_channel_logout(content_type=None)
    assert response.status_code == 400
