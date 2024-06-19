import uuid

import pytest
from django.contrib.auth import get_user_model

from helusers.user_utils import get_or_create_user, migrate_user
from helusers.utils import uuid_to_username


@pytest.fixture(autouse=True)
def setup_migrate(settings):
    settings.HELUSERS_USER_MIGRATE_ENABLED = True
    settings.HELUSERS_USER_MIGRATE_AMRS = ["a", "b"]
    settings.HELUSERS_USER_MIGRATE_EMAIL_DOMAINS = ["example.com", "example.org"]


@pytest.mark.parametrize(
    "migrate_enabled, amr, email, good_username, expect_migration",
    [
        pytest.param(True, ["a"], "auser@example.org", True, True, id="migrate"),
        pytest.param(
            True, ["a"], "auser@example.org", False, False, id="wrong_username"
        ),
        pytest.param(True, ["c"], "auser@example.org", True, False, id="wrong_amr"),
        pytest.param(True, ["a"], "auser@example.net", True, False, id="wrong_domain"),
        pytest.param(False, ["a"], "auser@example.org", True, False, id="disabled"),
    ],
)
@pytest.mark.django_db
def test_migrate_user(
    settings, migrate_enabled, amr, email, good_username, expect_migration
):
    settings.HELUSERS_USER_MIGRATE_ENABLED = migrate_enabled
    old_uuid = uuid.uuid4()
    new_uuid = uuid.uuid4()
    old_username = uuid_to_username(old_uuid) if good_username else str(old_uuid)
    user_model = get_user_model()
    user = user_model.objects.create(
        uuid=old_uuid,
        username=old_username,
        first_name="A",
        last_name="User",
        email=email,
    )

    payload = {
        "sub": str(new_uuid),
        "amr": amr,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }

    migrate_user(user_id=str(new_uuid), payload=payload)

    if expect_migration:
        user.refresh_from_db()
        assert user.uuid == new_uuid
        assert user.username == uuid_to_username(new_uuid)
    else:
        user.refresh_from_db()
        assert user.uuid == old_uuid
        assert user.username == old_username


@pytest.mark.parametrize(
    "migrate_enabled, amr, email, good_username, expect_migration",
    [
        pytest.param(True, ["a"], "auser@example.org", True, True, id="migrate"),
        pytest.param(
            True, ["a"], "auser@example.org", False, False, id="wrong_username"
        ),
        pytest.param(True, ["c"], "auser@example.org", True, False, id="wrong_amr"),
        pytest.param(True, ["a"], "auser@example.net", True, False, id="wrong_domain"),
        pytest.param(False, ["a"], "auser@example.org", True, False, id="disabled"),
    ],
)
@pytest.mark.django_db
def test_get_or_create_user_migrate_user(
    settings, migrate_enabled, amr, email, good_username, expect_migration
):
    settings.HELUSERS_USER_MIGRATE_ENABLED = migrate_enabled
    old_uuid = uuid.uuid4()
    new_uuid = uuid.uuid4()
    user_model = get_user_model()
    old_user = user_model.objects.create(
        uuid=old_uuid,
        username=uuid_to_username(old_uuid) if good_username else str(old_uuid),
        first_name="A",
        last_name="User",
        email=email,
    )

    payload = {
        "sub": str(new_uuid),
        "amr": amr,
        "email": old_user.email,
        "first_name": old_user.first_name,
        "last_name": old_user.last_name,
    }

    user = get_or_create_user(payload)

    if expect_migration:
        assert user_model.objects.count() == 1
        assert user.uuid == new_uuid
        assert user.username == uuid_to_username(new_uuid)
    else:
        assert user_model.objects.count() == 2
        assert user_model.objects.filter(uuid=old_uuid).exists()
        assert user.uuid == new_uuid
        assert user.username == uuid_to_username(new_uuid)
