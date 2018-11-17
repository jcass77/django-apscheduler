from datetime import datetime

from django.utils import timezone

from django_apscheduler import util


def test_get_format_default():
    assert util.get_format() == "N j, Y, f:s a"


def test_get_format_from_settings(use_seconds_format):
    assert util.get_format() == use_seconds_format


def test_localize_naive(use_hour_format):

    dt = datetime.utcnow()
    dt_hour = dt.strftime("%H")

    localized_dt_hour = util.localize(dt)

    assert localized_dt_hour == dt_hour


def test_localize_aware(use_tz):
    utc_dt = timezone.now()

    local_dt = timezone.localtime(utc_dt)
    local_dt_hour = local_dt.strftime("%H")

    localized_dt_hour = util.localize(utc_dt)

    assert localized_dt_hour == local_dt_hour
