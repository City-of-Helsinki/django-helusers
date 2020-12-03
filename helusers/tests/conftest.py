from datetime import datetime, timezone

import pytest


def unix_timestamp_now():
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    return int((datetime.now(tz=timezone.utc) - epoch).total_seconds())


@pytest.fixture(name="unix_timestamp_now")
def unix_timestamp_now_fixture():
    return unix_timestamp_now()
