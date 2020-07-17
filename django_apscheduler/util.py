from datetime import datetime

from django.conf import settings
from django.utils import formats
from django.utils import timezone


def uct_datetime_to_datetime(dt: datetime) -> datetime:
    """
    Converts datetime with timezone to datetime without timezone. This is required when receiving date times from
    APScheduler if the default Django settings.USE_TZ = False (i.e. timezone support is disabled) is being used.
    """
    if dt and not settings.USE_TZ and timezone.is_aware(dt):
        return timezone.make_naive(dt)

    return dt


def datetime_to_uct_datetime(dt: datetime) -> datetime:
    """
    Converts datetime without timezone to datetime with timezone. This is required when sending date times to
    APScheduler if the default ettings.USE_TZ = False (i.e. timezone support is disabled) is being used.
    """
    if dt and not settings.USE_TZ and timezone.is_naive(dt):
        return timezone.make_aware(dt)

    return dt


def get_dt_format() -> str:
    """Return the configured format for displaying datetimes in the Django admin views"""
    return formats.get_format(
        getattr(settings, "APSCHEDULER_DATETIME_FORMAT", "N j, Y, f:s a")
    )


def get_local_dt_format(dt: datetime) -> str:
    """Get the datetime in the localized datetime format"""
    if dt and settings.USE_TZ and timezone.is_aware(dt):
        dt = timezone.localtime(dt)

    return formats.date_format(dt, get_dt_format())
