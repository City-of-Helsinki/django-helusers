import datetime

import pytest

from helusers.sessions import TunnistamoOIDCSerializer


@pytest.mark.parametrize(
    "obj,expected",
    [
        (
            {"access_token_expires_at": datetime.datetime(2024, 3, 1, 15, 30, 1, 20)},
            "2024-03-01T15:30:01.000020",
        ),
        (
            {"access_token_expires_at": "2024-03-01T15:30:23.985377"},
            "2024-03-01T15:30:23.985377",
        ),
    ],
)
def test_datetime_field_is_serialized(obj, expected):
    serializer = TunnistamoOIDCSerializer()

    assert serializer.dumps(obj) == b'{"%s":"%s"}' % (
        serializer.datetime_field.encode(),
        expected.encode(),
    )


def test_datetime_field_is_deserialized():
    serializer = TunnistamoOIDCSerializer()
    data = b'{"%s":"2024-03-01T15:30:23.985377"}' % serializer.datetime_field.encode()

    assert serializer.loads(data) == {
        serializer.datetime_field: datetime.datetime(2024, 3, 1, 15, 30, 23, 985377)
    }
