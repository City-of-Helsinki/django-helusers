from datetime import datetime, timezone

import pytest
import responses


@pytest.fixture
def mock_responses():
    with responses.RequestsMock() as mock_resps:
        yield mock_resps


def unix_timestamp_now():
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    return int((datetime.now(tz=timezone.utc) - epoch).total_seconds())


@pytest.fixture(name="unix_timestamp_now")
def unix_timestamp_now_fixture():
    return unix_timestamp_now()
