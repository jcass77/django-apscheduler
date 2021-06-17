from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest
import pytz
from apscheduler.executors.debug import DebugExecutor
from apscheduler.job import Job
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from django import db
from django.db import transaction

from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJob


def raise_db_operational_error(*args, **kwargs):
    """Helper method for triggering a db.OperationalError as a side effect of executing mocked DB operations"""
    raise db.OperationalError("Some DB-related error")


class DummyScheduler(BaseScheduler):
    def __init__(self, *args, **kwargs):
        super(DummyScheduler, self).__init__(*args, **kwargs)
        self.wakeup = MagicMock()

    def shutdown(self, wait=True):
        super(DummyScheduler, self).shutdown(wait)

    def wakeup(self):
        self._process_jobs()


def dummy_job():
    pass


@pytest.fixture
def timezone(monkeypatch, settings):
    # Based on https://github.com/agronholm/apscheduler/blob/8235c03d790b42104e2921d9cff376c9f53dd53d/tests/conftest.py#L43
    tz = pytz.timezone(settings.TIME_ZONE)
    monkeypatch.setattr(
        "apscheduler.schedulers.base.get_localzone", Mock(return_value=tz)
    )
    return tz


@pytest.fixture
def job_defaults(timezone):
    # Based on https://github.com/agronholm/apscheduler/blob/8235c03d790b42104e2921d9cff376c9f53dd53d/tests/conftest.py#L82
    run_date = timezone.localize(datetime(2011, 4, 3, 18, 40))
    return {
        "trigger": "date",
        "trigger_args": {"run_date": run_date, "timezone": timezone},
        "executor": "default",
        "args": (),
        "kwargs": {},
        "id": b"t\xc3\xa9st\xc3\xafd".decode("utf-8"),
        "misfire_grace_time": 1,
        "coalesce": False,
        "name": b"n\xc3\xa4m\xc3\xa9".decode("utf-8"),
        "max_instances": 1,
    }


@pytest.fixture
def create_job(job_defaults, timezone):
    # Based on https://github.com/agronholm/apscheduler/blob/8235c03d790b42104e2921d9cff376c9f53dd53d/tests/conftest.py#L91
    def create(**kwargs):
        kwargs.setdefault("scheduler", Mock(BaseScheduler, timezone=timezone))
        job_kwargs = job_defaults.copy()
        job_kwargs.update(kwargs)
        job_kwargs["trigger"] = BlockingScheduler()._create_trigger(
            job_kwargs.pop("trigger"), job_kwargs.pop("trigger_args")
        )
        job_kwargs.setdefault("next_run_time", None)
        return Job(**job_kwargs)

    return create


@pytest.fixture
def create_add_job(timezone, create_job):
    # Based on https://github.com/agronholm/apscheduler/blob/8235c03d790b42104e2921d9cff376c9f53dd53d/tests/test_jobstores.py#L101
    def create(
        jobstore,
        func=dummy_job,
        run_date=datetime(2999, 1, 1),
        id=None,
        paused=False,
        **kwargs
    ):
        run_date = timezone.localize(run_date)
        job = create_job(
            func=func,
            trigger="date",
            trigger_args={"run_date": run_date},
            id=id,
            **kwargs
        )
        job.next_run_time = (
            None if paused else job.trigger.get_next_fire_time(None, run_date)
        )
        if jobstore:
            jobstore.add_job(job)
        return job

    return create


@pytest.fixture
def jobstore():
    # Based on https://github.com/agronholm/apscheduler/blob/8235c03d790b42104e2921d9cff376c9f53dd53d/tests/test_jobstores.py#L57
    store = DjangoJobStore()
    store.start(DummyScheduler(), "djangojobstore")
    yield store
    transaction.on_commit(DjangoJob.objects.all().delete)
    store.shutdown()


@pytest.fixture
def scheduler(jobstore, settings):
    scheduler = DummyScheduler(timezone=settings.TIME_ZONE)
    scheduler.add_jobstore(jobstore, "default")
    scheduler.add_executor(DebugExecutor())

    return scheduler


@pytest.fixture
def use_seconds_format(settings):
    settings.APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s"
    return settings.APSCHEDULER_DATETIME_FORMAT


@pytest.fixture
def use_tz(settings):
    settings.APSCHEDULER_DATETIME_FORMAT = "H"  # Only interested in hour
    settings.USE_TZ = True

    return settings.APSCHEDULER_DATETIME_FORMAT


@pytest.fixture
def use_hour_format(settings):
    settings.APSCHEDULER_DATETIME_FORMAT = "H"  # Only interested in hour

    return settings.APSCHEDULER_DATETIME_FORMAT
