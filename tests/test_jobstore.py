from __future__ import print_function

import datetime
import logging

import pytest
from apscheduler.events import JobExecutionEvent, JobSubmissionEvent
from apscheduler.executors.debug import DebugExecutor
from apscheduler.schedulers.base import BaseScheduler
from django.db import connection, transaction
from django.db.backends.utils import CursorWrapper
from django.db.models.sql.compiler import SQLCompiler
from django.db.utils import OperationalError
from pytz import utc

from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job
from django_apscheduler.models import DjangoJob, DjangoJobExecution, DjangoJobManager
from django_apscheduler.result_storage import DjangoResultStorage
from django_apscheduler.util import serialize_dt
from tests.compat import mock_compat

logging.basicConfig()


class DebugScheduler(BaseScheduler):

    def shutdown(self, wait=True):
        pass

    def wakeup(self):
        pass


@pytest.fixture()
def scheduler():
    scheduler = DebugScheduler()
    scheduler.add_jobstore(DjangoJobStore())
    scheduler.add_executor(DebugExecutor())

    return scheduler


def job(*args, **kwargs):
    print("JOB")


def test_add_job(db, scheduler):
    """
    :type scheduler: DebugScheduler
    """

    scheduler.add_job(job, trigger="interval", seconds=1, id="job")

    scheduler.start()

    assert DjangoJob.objects.count() == 1

    # add job second time
    scheduler.add_job(job, trigger="interval", seconds=1, id="job", replace_existing=True)

    assert DjangoJob.objects.count() == 1

def test_issue_20(db, scheduler):
    assert isinstance(scheduler, DebugScheduler)
    scheduler.add_job(job, trigger="interval", seconds=1, id="job")
    scheduler.start()
    assert DjangoJob.objects.count() == 1
    scheduler.remove_job("job")
    assert DjangoJob.objects.count() == 0


@pytest.mark.target
def test_remove_job(db, scheduler):
    """ This test checks issue https://github.com/jarekwg/django-apscheduler/issues/6 """

    assert isinstance(scheduler, DebugScheduler)
    scheduler.add_job(job, trigger="interval", seconds=1, id="job")
    scheduler.start()

    assert DjangoJob.objects.count() == 1
    assert isinstance(scheduler, DebugScheduler)
    assert len(scheduler.get_jobs()) == 1

    dbJob = DjangoJob.objects.first()
    dbJob.delete()

    assert len(scheduler.get_jobs()) == 0


def test_register_job_dec(db, scheduler):

    register_job(scheduler, "interval", seconds=1)(job)

    scheduler.start()

    assert DjangoJob.objects.count() == 1
    dbj = DjangoJob.objects.first()
    assert dbj.name == "tests.test_jobstore.job"

    j = scheduler.get_jobs()[0]
    assert j.id == "tests.test_jobstore.job"


def test_job_events(db, scheduler):
    register_events(scheduler)
    scheduler.add_job(job, trigger="interval", seconds=1, id="job")
    scheduler.start()

    dj = DjangoJob.objects.last()
    dj.next_run_time -= datetime.timedelta(seconds=2)
    dj.save()

    now = datetime.datetime.now(utc)
    scheduler._dispatch_event(JobExecutionEvent(4096, "job", None, now))
    scheduler._dispatch_event(JobSubmissionEvent(32768, "job", None, [now]))

    assert DjangoJobExecution.objects.count() == 1


def test_issue_15(db):
    """
    This test covers bug from https://github.com/jarekwg/django-apscheduler/issues/15
    """

    storage = DjangoResultStorage()

    srt = datetime.datetime.now()

    job = DjangoJob.objects.create(name="test", next_run_time=datetime.datetime.now())
    DjangoJobExecution.objects.create(
        job=job,
        run_time=serialize_dt(srt)
    )

    storage.get_or_create_job_execution(
        job,
        mock_compat.Mock(scheduled_run_times=[srt])
    )


def test_reconnect_on_db_error(transactional_db):

    counter = [0]
    def mocked_execute(self, *a, **k):
        counter[0] += 1

        if counter[0] == 1:
            raise OperationalError()
        else:
            return []

    with mock_compat.patch.object(CursorWrapper, "execute", mocked_execute):
        store = DjangoJobStore()
        DjangoJob.objects._last_ping = 0

        assert store.get_due_jobs(now=datetime.datetime.now()) == []

