import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

from helusers._oidc_auth_impl import ApiTokenAuthentication
from helusers.tests.test_jwt_token_authentication import (  # noqa: F401
    authentication_passes,
    auto_auth_server,
    do_authentication,
    USER_UUID,
)


class ReturnValueChangeApiTokenAuthentication(ApiTokenAuthentication):
    def authenticate(self, request, **kwargs):
        user_auth_tuple = super().authenticate(request)
        if not user_auth_tuple:
            return None
        user, auth = user_auth_tuple
        return user


@pytest.mark.django_db
def test_overriden_authenticate_method_works():
    """Tests that subclasses that override authenticate method still work

    Some projects use ApiTokenAuthentication with GraphlQL where the authenticator
    should only return user and not a "user, auth"-tuple."""
    result = do_authentication(sut=ReturnValueChangeApiTokenAuthentication())
    assert isinstance(result, get_user_model())
    assert result.uuid == USER_UUID


class AmrFixApiTokenAuthentication(ApiTokenAuthentication):
    def __convert_amr_to_list(self, id_token):
        if id_token["amr"] and not isinstance(id_token["amr"], list):
            id_token["amr"] = [id_token["amr"]]

    def validate_claims(self, id_token):
        self.__convert_amr_to_list(id_token)
        super().validate_claims(id_token)


@pytest.mark.django_db
def test_overridden_validate_claims_method_works():
    """Tests that subclasses that override validate_claims method still work

    The ApiTokenAuthentication.validate_claims is no longer used but previously some
    projects overrode it to fix incorrect amr-claim Tunnistamo sets. The amr fix is
    no longer necessary because amr claim is no longer validated at all."""
    authentication_passes(sut=AmrFixApiTokenAuthentication(), amr="test_value")


# From https://github.com/City-of-Helsinki/kerrokantasi/blob/master/kerrokantasi/oidc.py
class KerroKantasiApiTokenAuthentication(ApiTokenAuthentication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def authenticate(self, request):
        jwt_value = self.get_jwt_value(request)
        if jwt_value is None:
            return None

        payload = self.decode_jwt(jwt_value)
        user, auth = super().authenticate(request)

        # amr (Authentication Methods References) should contain the used auth
        # provider name e.g. suomifi
        if payload.get("amr") in settings.STRONG_AUTH_PROVIDERS:
            user.has_strong_auth = True
        else:
            user.has_strong_auth = False

        user.save()
        return (user, auth)


@pytest.mark.django_db
@pytest.mark.parametrize("amr", [None, "suomifi"])
def test_kerrokantasi_apitokenauthentication_works(settings, amr):
    settings.STRONG_AUTH_PROVIDERS = ["suomifi"]
    auth = do_authentication(sut=KerroKantasiApiTokenAuthentication(), amr=amr)

    assert auth.user.has_strong_auth == bool(amr)
