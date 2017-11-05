from __future__ import print_function

import datetime
import logging

import pytest
from apscheduler.events import JobExecutionEvent, JobSubmissionEvent
from apscheduler.executors.debug import DebugExecutor
from apscheduler.schedulers.base import BaseScheduler
from pytz import utc

from django_apscheduler.jobstores import DjangoJobStore, register_events
from django_apscheduler.models import DjangoJob, DjangoJobExecution

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
