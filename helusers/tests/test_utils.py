import pytest
import random
from uuid import UUID
from helusers.utils import uuid_to_username, username_to_uuid


def test_uuid_to_username():
    assert uuid_to_username('00fbac99-0bab-5e66-8e84-2e567ea4d1f6') == 'u-ad52zgilvnpgnduefzlh5jgr6y'


def test_username_to_uuid():
    assert username_to_uuid('u-ad52zgilvnpgnduefzlh5jgr6y') == UUID('00fbac99-0bab-5e66-8e84-2e567ea4d1f6')


def test_reflective_username_uuid_relationship():
    rd = random.Random()
    rd.seed(0)

    for uuid in [UUID(int=rd.getrandbits(128)) for i in range(0,100)]:
        assert username_to_uuid(uuid_to_username(uuid)) == uuid
