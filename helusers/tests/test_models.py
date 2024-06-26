import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from helusers.jwt import JWT
from helusers.models import ADGroup, ADGroupMapping, OIDCBackChannelLogoutEvent

from .conftest import encoded_jwt_factory, ISSUER1

user_model = get_user_model()


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


@pytest.mark.django_db
class TestUserAdGroups:
    ALL_AD_GROUPS_MAPPING = (
        ("ad_group_1", "group_1"),
        ("ad_group_2", "group_2"),
        ("ad_group_3", "group_3"),
    )
    ALL_AD_GROUP_NAMES = ("ad_group_1", "ad_group_2", "ad_group_3")
    ALL_GROUP_NAMES = ("group_1", "group_2", "group_3")

    @pytest.mark.parametrize(
        "ad_group_mapping,old_ad_groups_names,old_groups_names,new_ad_groups_names,new_groups_names",
        [
            # Nothing changes
            pytest.param(
                ALL_AD_GROUPS_MAPPING,
                ALL_AD_GROUP_NAMES,
                ALL_GROUP_NAMES,
                ALL_AD_GROUP_NAMES,
                ALL_GROUP_NAMES,
                id="nothing_changes",
            ),
            # If not mapped, not added
            pytest.param(
                (("ad_group_1", "group_1"),),
                ("ad_group_1",),
                ("group_1",),
                ALL_AD_GROUP_NAMES,
                ("group_1",),
                id="not_mapped_not_added",
            ),
            # New ones are added
            pytest.param(
                ALL_AD_GROUPS_MAPPING,
                ("ad_group_1",),
                ("group_1",),
                ALL_AD_GROUP_NAMES,
                ALL_GROUP_NAMES,
                id="new_added",
            ),
            # Old ones are removed
            pytest.param(
                ALL_AD_GROUPS_MAPPING,
                ALL_AD_GROUP_NAMES,
                ALL_GROUP_NAMES,
                ("ad_group_1",),
                ("group_1",),
                id="old_removed",
            ),
            # Mapped twice, given once
            pytest.param(
                (
                    ("ad_group_1", "group_1"),
                    ("ad_group_1_1", "group_1"),
                    ("ad_group_2", "group_2"),
                    ("ad_group_2_2", "group_2"),
                    ("ad_group_3", "group_3"),
                ),
                ALL_AD_GROUP_NAMES,
                ALL_GROUP_NAMES,
                ALL_AD_GROUP_NAMES,
                ALL_GROUP_NAMES,
                id="mapped_twice_given_once",
            ),
            # Mapped twice, given twice & 1 removed.
            pytest.param(
                (
                    ("ad_group_1", "group_1"),
                    ("ad_group_1_1", "group_1"),
                    ("ad_group_2", "group_2"),
                    ("ad_group_2_2", "group_2"),
                    ("ad_group_3", "group_3"),
                ),
                ALL_AD_GROUP_NAMES,
                ALL_GROUP_NAMES,
                (
                    "ad_group_1",
                    "ad_group_1_1",
                    "ad_group_2",
                ),
                ("group_1", "group_2"),
                id="mapped_twice_given_twice",
            ),
            # All mapped, empty list given: All should be removed.
            pytest.param(
                ALL_AD_GROUPS_MAPPING,
                ALL_AD_GROUP_NAMES,
                ALL_GROUP_NAMES,
                [],
                [],
                id="all_removed",
            ),
        ],
    )
    def test_update_ad_groups(
        self,
        ad_group_mapping,
        old_ad_groups_names,
        old_groups_names,
        new_ad_groups_names,
        new_groups_names,
    ):
        # Setup ad groups mapping
        ADGroupMapping.objects.bulk_create(
            [
                ADGroupMapping(
                    ad_group=ADGroup.objects.get_or_create(
                        name=ad_group_name, display_name=ad_group_name
                    )[0],
                    group=Group.objects.get_or_create(name=group_name)[0],
                )
                for ad_group_name, group_name in ad_group_mapping
            ]
        )

        # Setup existing AD-groups
        old_ad_groups = [
            ADGroup.objects.get_or_create(name=name, display_name=name)[0]
            for name in old_ad_groups_names
        ]

        # Setup existing groups
        old_groups = [
            Group.objects.get_or_create(name=name)[0] for name in old_groups_names
        ]

        # Setup a user
        user = user_model.objects.create(username="testguy")
        user.ad_groups.set(old_ad_groups)
        user.groups.set(old_groups)
        user.save()

        # Expect that the ad groups and groups are persisted to the user instance
        assert ADGroupMapping.objects.count() == len(ad_group_mapping)
        assert user.ad_groups.count() == len(old_ad_groups_names)
        assert user.groups.count() == len(old_groups_names)

        # When user update_ad_groups is called
        user.update_ad_groups(ad_group_names=new_ad_groups_names)

        # Then user has a new set of groups
        assert sorted([ad_group.name for ad_group in user.ad_groups.all()]) == list(
            new_ad_groups_names
        )
        assert sorted([group.name for group in user.groups.all()]) == list(
            new_groups_names
        )
