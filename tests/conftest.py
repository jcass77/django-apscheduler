from unittest.mock import MagicMock

import pytest
from apscheduler.executors.debug import DebugExecutor
from apscheduler.schedulers.base import BaseScheduler
from django.conf import settings
from django.utils import timezone

from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution


class DummyScheduler(BaseScheduler):
    def __init__(self, *args, **kwargs):
        super(DummyScheduler, self).__init__(*args, **kwargs)
        self.wakeup = MagicMock()

    def shutdown(self, wait=True):
        super(DummyScheduler, self).shutdown(wait)

    def wakeup(self):
        self._process_jobs()


def dummy_job(*args, **kwargs):
    print(f"Dummy job called at {timezone.now()}")


@pytest.fixture
def job():
    return dummy_job


@pytest.fixture
def djangojobstore():
    store = DjangoJobStore()
    # store.start(None, "django")
    yield store
    store.shutdown()

    DjangoJobExecution.objects.all().delete()


@pytest.fixture
def scheduler(djangojobstore):
    scheduler = DummyScheduler(timezone=settings.TIME_ZONE)
    scheduler.add_jobstore(djangojobstore, "default")
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
