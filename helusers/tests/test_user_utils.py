import uuid

import pytest

from helusers.user_utils import get_or_create_user


@pytest.mark.django_db
def test_get_or_create_user_always_returns_a_User_with_UUID_type_id():
    user_uuid = uuid.uuid4()
    payload = {
        "sub": str(user_uuid),
    }

    user1 = get_or_create_user(payload)
    user2 = get_or_create_user(payload)

    assert user1.uuid == user_uuid
    assert user2.uuid == user_uuid
    assert user1 == user2
