import datetime
import logging
from unittest import mock

from apscheduler import events
from apscheduler.events import JobExecutionEvent, JobSubmissionEvent
from django.db.backends.utils import CursorWrapper
from django.db.utils import OperationalError
from django.utils import timezone

from django_apscheduler.jobstores import (
    DjangoJobStore,
    register_job,
)
from django_apscheduler.models import DjangoJob, DjangoJobExecution
from django_apscheduler.util import get_django_internal_datetime

logging.basicConfig()


def test_add_job(db, job, scheduler):
    scheduler.add_job(job, trigger="interval", seconds=1, id="job")

    scheduler.start()

    assert DjangoJob.objects.count() == 1

    # Add job second time
    scheduler.add_job(
        job, trigger="interval", seconds=1, id="job", replace_existing=True
    )

    assert DjangoJob.objects.count() == 1


def test_issue_20(db, job, scheduler):
    scheduler.add_job(job, trigger="interval", seconds=1, id="job")
    scheduler.start()

    assert DjangoJob.objects.count() == 1

    scheduler.remove_job("job")

    assert DjangoJob.objects.count() == 0


def test_remove_job(db, job, scheduler):
    """ This test checks issue https://github.com/jarekwg/django-apscheduler/issues/6 """

    scheduler.add_job(job, trigger="interval", seconds=1, id="job")
    scheduler.start()

    assert DjangoJob.objects.count() == 1
    assert len(scheduler.get_jobs()) == 1

    dbJob = DjangoJob.objects.first()
    dbJob.delete()

    assert len(scheduler.get_jobs()) == 0


def job_for_tests():
    job_for_tests.mock()


job_for_tests.mock = mock.Mock()


def test_try_add_job_then_start(db, scheduler):
    scheduler.add_job(
        job_for_tests, next_run_time=timezone.now(), misfire_grace_time=None,
    )
    scheduler.start()
    scheduler._process_jobs()

    assert job_for_tests.mock.call_count == 1


def test_register_job_dec(db, job, scheduler):
    register_job(scheduler, "interval", seconds=1)(job)

    scheduler.start()

    assert DjangoJob.objects.count() == 1

    dbj = DjangoJob.objects.first()

    assert dbj.id == "tests.conftest.dummy_job"

    j = scheduler.get_jobs()[0]

    assert j.id == "tests.conftest.dummy_job"


def test_job_events(db, job, djangojobstore, scheduler):
    scheduler.add_job(job, trigger="interval", seconds=1, id="job")
    scheduler.start()

    dj = DjangoJob.objects.last()
    dj.next_run_time -= datetime.timedelta(seconds=2)
    dj.save()

    now = timezone.now()
    scheduler._dispatch_event(
        JobSubmissionEvent(events.EVENT_JOB_SUBMITTED, "job", djangojobstore, [now])
    )
    scheduler._dispatch_event(
        JobExecutionEvent(events.EVENT_JOB_EXECUTED, "job", djangojobstore, now)
    )

    assert DjangoJobExecution.objects.count() == 1


def test_issue_15(db, djangojobstore):
    """
    This test covers bug from https://github.com/jarekwg/django-apscheduler/issues/15
    """
    srt = timezone.now()

    job = DjangoJob.objects.create(id="test", next_run_time=timezone.now())
    DjangoJobExecution.objects.create(
        job=job, run_time=get_django_internal_datetime(srt)
    )

    djangojobstore.handle_submission_event(
        mock.Mock(
            spec=JobSubmissionEvent,
            job_id=job.id,
            code=events.EVENT_JOB_SUBMITTED,
            scheduled_run_times=[srt],
        )
    )


def test_reconnect_on_db_error(transactional_db):
    counter = [0]

    def mocked_execute(self, *a, **k):
        counter[0] += 1

        if counter[0] == 1:
            raise OperationalError()
        else:
            return []

    with mock.patch.object(CursorWrapper, "execute", mocked_execute):
        store = DjangoJobStore()
        # DjangoJob.objects._last_ping = 0

        assert store.get_due_jobs(now=timezone.now()) == []
