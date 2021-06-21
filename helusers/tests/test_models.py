import pytest

from helusers.jwt import JWT
from helusers.models import OIDCBackChannelLogoutEvent

from .conftest import encoded_jwt_factory, ISSUER1


@pytest.mark.django_db
class TestOIDCBackChannelLogoutEvent:
    @pytest.mark.parametrize("logout_sub", ["logout_sub_value", "", None])
    @pytest.mark.parametrize("token_sub", ["token_sub_value", "", None])
    def test_when_iss_and_sid_claims_match_then_token_session_is_considered_terminated(
        self, logout_sub, token_sub
    ):
        sid = "sid_value"

        logout_token = JWT(encoded_jwt_factory(iss=ISSUER1, sub=logout_sub, sid=sid))
        OIDCBackChannelLogoutEvent.objects.logout_token_received(logout_token)

        token = JWT(encoded_jwt_factory(iss=ISSUER1, sub=token_sub, sid=sid))
        assert (
            OIDCBackChannelLogoutEvent.objects.is_session_terminated_for_token(token)
            is True
        )

    @pytest.mark.parametrize("logout_sid", ["", None])
    @pytest.mark.parametrize("token_sid", ["token_sid_value", "", None])
    def test_when_logout_token_sid_claim_is_empty_then_no_token_session_is_considered_terminated(
        self, logout_sid, token_sid
    ):
        sub = "sub_value"

        logout_token = JWT(encoded_jwt_factory(iss=ISSUER1, sub=sub, sid=logout_sid))
        OIDCBackChannelLogoutEvent.objects.logout_token_received(logout_token)

        token = JWT(encoded_jwt_factory(iss=ISSUER1, sub=sub, sid=token_sid))
        assert (
            OIDCBackChannelLogoutEvent.objects.is_session_terminated_for_token(token)
            is False
        )

    def test_when_a_session_is_terminated_then_tokens_for_another_session_are_not_affected(
        self,
    ):
        sub = "sub_value"

        logout_token = JWT(encoded_jwt_factory(iss=ISSUER1, sub=sub, sid="sid_value"))
        OIDCBackChannelLogoutEvent.objects.logout_token_received(logout_token)

        token = JWT(encoded_jwt_factory(iss=ISSUER1, sub=sub, sid="other_sid_value"))
        assert (
            OIDCBackChannelLogoutEvent.objects.is_session_terminated_for_token(token)
            is False
        )

    def test_receiving_the_same_logout_token_more_than_once_has_no_effect(self):
        logout_token = JWT(
            encoded_jwt_factory(iss=ISSUER1, sub="sub_value", sid="sid_value")
        )
        OIDCBackChannelLogoutEvent.objects.logout_token_received(logout_token)
        OIDCBackChannelLogoutEvent.objects.logout_token_received(logout_token)

        assert OIDCBackChannelLogoutEvent.objects.count() == 1
