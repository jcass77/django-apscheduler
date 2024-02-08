from datetime import datetime
from unittest import mock

import pytest
import pytz
from django import db

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


@pytest.mark.django_db
def test_retry_on_db_operational_error_no_db_errors(caplog):
    @util.retry_on_db_operational_error
    def dummy_db_op():
        return

    with mock.patch.object(db.connection, "close") as close_mock:
        dummy_db_op()
        assert not close_mock.called

    assert "Retrying with a new DB connection..." not in caplog.text


@pytest.mark.django_db
def test_retry_on_db_operational_error_db_operational_error_retry_ok(caplog):
    def dummy_func_maker():
        call_count = 0

        @util.retry_on_db_operational_error
        def dummy_db_op():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Raise exception on first call
                raise db.OperationalError("Some DB-related error")

            return call_count

        return dummy_db_op

    func = dummy_func_maker()
    with mock.patch.object(db.connection, "close") as close_mock:
        call_count = func()
        assert call_count == 2
        assert close_mock.call_count == 1

    assert (
            "DB error executing 'dummy_db_op' (Some DB-related error). Retrying with a new DB connection..."
            in caplog.text
    )


@pytest.mark.django_db
def test_retry_on_db_operational_error_db_operational_error_retry_error_persists_re_raises(
        caplog,
):
    @util.retry_on_db_operational_error
    def func():
        raise db.OperationalError("Some DB-related error")

    with mock.patch.object(db.connection, "close") as close_mock:
        with pytest.raises(db.OperationalError, match="Some DB-related error"):
            call_count = func()
            assert call_count == 2

        assert close_mock.call_count == 1

    assert (
            "DB error executing 'func' (Some DB-related error). Retrying with a new DB connection..."
            in caplog.text
    )


@pytest.mark.django_db
def test_retry_on_db_operational_error_non_db_operational_error_re_raises(
        caplog,
):
    @util.retry_on_db_operational_error
    def func():
        raise RuntimeError("Some non DB-related error")

    with mock.patch.object(db.connection, "close") as close_mock:
        with pytest.raises(RuntimeError, match="Some non DB-related error"):
            func()

        assert not close_mock.called

    assert (
            "DB error executing 'dummy_db_op' (Some DB-related error). Retrying with a new DB connection..."
            not in caplog.text
    )


def test_close_old_connections_calls_close_old_connections():
    @util.close_old_connections
    def job_mock():
        pass

    with mock.patch(
            "django_apscheduler.util.db.close_old_connections"
    ) as close_old_connections_mock:
        job_mock()

    assert close_old_connections_mock.call_count == 2


def test_close_old_connections_even_if_exception_is_raised():
    @util.close_old_connections
    def job_mock():
        raise RuntimeError("some error")

    with mock.patch(
            "django_apscheduler.util.db.close_old_connections"
    ) as close_old_connections_mock:
        with pytest.raises(RuntimeError, match="some error"):
            job_mock()

    assert close_old_connections_mock.call_count == 2
