from __future__ import print_function

from threading import Thread

import pytest
from apscheduler import events
from apscheduler.events import JobEvent, JobExecutionEvent
from apscheduler.executors.base import BaseExecutor
from apscheduler.executors.debug import DebugExecutor
from apscheduler.schedulers.base import BaseScheduler

from django_apscheduler.jobstores import DjangoJobStore, register_events
from django_apscheduler.models import DjangoJob, DjangoJobExecution

import logging
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

def test_delete_dbjob_cause_job_delete(db, scheduler):
    """
    :type scheduler: DebugScheduler
    """
    scheduler.start()
    scheduler.add_job(job, trigger="interval", seconds=1, id="job")

    assert DjangoJob.objects.count() == 1
    assert len(scheduler.get_jobs()) == 1

    DjangoJob.objects.first().delete()

    assert len(scheduler.get_jobs()) == 0


def test_job_execution_events(db, scheduler):
    ":type scheduler: DebugScheduler"
    assert DjangoJobExecution.objects.count() == 0

    register_events(scheduler)

    scheduler.start()

    scheduler.add_job(job, trigger="interval", seconds=1, id="job")

    ex = scheduler._executors["default"]    #type: BaseExecutor

    ex.submit_job(scheduler.get_job("job"), [])

    def make_checks(checks, counts=1):
        assert DjangoJobExecution.objects.count() == counts
        d = DjangoJobExecution.objects.first()
        for key, value in checks.items():
            assert getattr(d, key) == value

    make_checks(dict(status=DjangoJobExecution.SUCCESS))
