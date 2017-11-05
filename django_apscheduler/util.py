from django.conf import settings
from django.utils.timezone import is_aware, is_naive, make_aware, make_naive


def serialize_dt(dt):
    """
    Converts datetime with timezone to datetime without timezone if USE_TZ is False
    :param dt:
    :return:
    """
    if not settings.USE_TZ and is_aware(dt):
        return make_naive(dt)
    return dt


def deserialize_dt(dt):
    if not settings.USE_TZ and is_naive(dt):
        return make_aware(dt)
    return dt
