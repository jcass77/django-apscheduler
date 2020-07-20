from datetime import datetime

from apscheduler.schedulers.base import BaseScheduler
from django.conf import settings
from django.utils import formats
from django.utils import timezone


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


def get_django_internal_datetime(dt: datetime) -> datetime:
    """
    Get the naive or aware version of the datetime based on the configured `USE_TZ` Django setting. This is also the
    format that Django uses to store datetimes internally.
    """
    if dt:
        if settings.USE_TZ and timezone.is_naive(dt):
            return timezone.make_aware(dt)

        elif not settings.USE_TZ and timezone.is_aware(dt):
            return timezone.make_naive(dt)

    return dt


def get_apscheduler_datetime(dt: datetime, scheduler: BaseScheduler) -> datetime:
    """
    Make the datetime timezone aware (if necessary), using the same timezone as is currently configured for the
    scheduler.
    """
    if dt and timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone=scheduler.timezone)

    return dt
