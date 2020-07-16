import pytest
import pytz
from apscheduler.executors.debug import DebugExecutor
from apscheduler.schedulers.base import BaseScheduler
from django.conf import settings

from django_apscheduler.jobstores import DjangoJobStore


class DebugScheduler(BaseScheduler):
    def shutdown(self, wait=True):
        pass

    def wakeup(self):
        self._process_jobs()


def job(*args, **kwargs):
    print("JOB")


@pytest.fixture
def scheduler():
    scheduler = DebugScheduler(timezone=pytz.timezone("Europe/Moscow"))
    scheduler.add_jobstore(DjangoJobStore())
    scheduler.add_executor(DebugExecutor())

    return scheduler


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
