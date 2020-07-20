from datetime import datetime

import pytest
import pytz
from django.utils import timezone

from django_apscheduler import util


def test_get_dt_format_default():
    assert util.get_dt_format() == "N j, Y, f:s a"


def test_get_dt_format_gets_format_from_settings(use_seconds_format):
    assert util.get_dt_format() == use_seconds_format


def test_get_local_dt_format_naive(use_hour_format):

    dt = datetime.utcnow()
    dt_hour = dt.strftime("%H")

    localized_dt_hour = util.get_local_dt_format(dt)

    assert localized_dt_hour == dt_hour


def test_get_local_dt_format_aware(use_tz):
    utc_dt = timezone.now()

    local_dt = timezone.localtime(utc_dt)
    local_dt_hour = local_dt.strftime("%H")

    localized_dt_hour = util.get_local_dt_format(utc_dt)

    assert localized_dt_hour == local_dt_hour


def test_get_django_internal_datetime_makes_naive_if_django_timzone_support_disabled(
    settings,
):
    settings.USE_TZ = False
    internal_dt = util.get_django_internal_datetime(datetime.now(tz=pytz.utc))

    assert timezone.is_naive(internal_dt)


def test_get_django_internal_datetime_makes_aware_if_django_timezone_support_enabled(
    settings,
):
    settings.USE_TZ = True
    internal_dt = util.get_django_internal_datetime(datetime.now())

    assert timezone.is_aware(internal_dt)


@pytest.mark.django_db
def test_get_apscheduler_datetime(scheduler):
    apscheduler_dt = util.get_apscheduler_datetime(datetime.now(), scheduler)

    assert timezone.is_aware(apscheduler_dt)
