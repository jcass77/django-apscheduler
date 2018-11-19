from django.conf import settings
from django.utils import formats
from django.utils import timezone


def serialize_dt(dt):
    """
    Converts datetime with timezone to datetime without timezone if USE_TZ is False
    :param dt:
    :return:
    """
    if not settings.USE_TZ and dt and timezone.is_aware(dt):
        return timezone.make_naive(dt)
    return dt


def deserialize_dt(dt):
    if not settings.USE_TZ and dt and timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return dt


def get_format():
    return formats.get_format(getattr(settings, "APSCHEDULER_DATETIME_FORMAT", "N j, Y, f:s a"))


def localize(dt):
    if settings.USE_TZ and dt and timezone.is_aware(dt):
        dt = timezone.localtime(dt)

    return formats.date_format(dt, get_format())
