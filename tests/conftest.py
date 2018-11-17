import pytest
from django.conf import settings


@pytest.fixture
def use_seconds_format():
    settings.APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s"
    return settings.APSCHEDULER_DATETIME_FORMAT


@pytest.fixture
def use_tz():
    settings.APSCHEDULER_DATETIME_FORMAT = "H"  # Only interested in hour
    settings.USE_TZ = True

    return settings.APSCHEDULER_DATETIME_FORMAT


@pytest.fixture
def use_hour_format():
    settings.APSCHEDULER_DATETIME_FORMAT = "H"  # Only interested in hour

    return settings.APSCHEDULER_DATETIME_FORMAT
