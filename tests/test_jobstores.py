import warnings
from datetime import datetime
from unittest import mock

import pytest
from apscheduler import events
from apscheduler.events import JobExecutionEvent, JobSubmissionEvent
from django import db
from django.utils import timezone

from django_apscheduler.jobstores import (
    DjangoJobStore,
    register_job,
    register_events,
)
from django_apscheduler.models import DjangoJob, DjangoJobExecution
from tests import conftest
from tests.conftest import DummyScheduler, dummy_job


class TestDjangoResultStoreMixin:
    def test_start_gets_scheduler_lock(self):
        store = DjangoJobStore()

        store.start(DummyScheduler(), "djangojobstore")
        assert store.lock is not None

    @pytest.mark.django_db
    def test_handle_submission_event_not_supported_raises_exception(self, jobstore):
        event = JobSubmissionEvent(
            events.EVENT_ALL, "test_job", jobstore, [timezone.now()]
        )

        with pytest.raises(NotImplementedError):
            jobstore.handle_submission_event(event)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "event_code",
        [
            events.EVENT_JOB_SUBMITTED,
            events.EVENT_JOB_MAX_INSTANCES,
        ],
    )
    def test_handle_submission_event_creates_job_execution(
            self, event_code, jobstore, create_add_job
    ):
        job = create_add_job(jobstore, dummy_job, datetime(2016, 5, 3))
        event = JobSubmissionEvent(event_code, job.id, jobstore, [timezone.now()])
        jobstore.handle_submission_event(event)

        assert DjangoJobExecution.objects.filter(job_id=event.job_id).exists()

    @pytest.mark.django_db(transaction=True)
    def test_handle_submission_event_for_job_that_no_longer_exists_does_not_raise_exception(
            self, jobstore
    ):
        event = JobSubmissionEvent(
            events.EVENT_JOB_SUBMITTED, "finished_job", jobstore, [timezone.now()]
        )
        jobstore.handle_submission_event(event)

        assert not DjangoJobExecution.objects.filter(job_id=event.job_id).exists()

    @pytest.mark.django_db
    def test_handle_execution_event_not_supported_raises_exception(self, jobstore):
        event = JobExecutionEvent(
            events.EVENT_ALL, "test_job", jobstore, timezone.now()
        )

        with pytest.raises(NotImplementedError):
            jobstore.handle_execution_event(event)

    @pytest.mark.django_db
    def test_handle_execution_event_creates_job_execution(
        self, jobstore, create_add_job
    ):
        job = create_add_job(jobstore, dummy_job, datetime(2016, 5, 3))
        event = JobExecutionEvent(
            events.EVENT_JOB_EXECUTED, job.id, jobstore, timezone.now()
        )
        jobstore.handle_execution_event(event)

        assert DjangoJobExecution.objects.filter(job_id=event.job_id).exists()

    @pytest.mark.django_db(transaction=True)
    def test_handle_execution_event_for_job_that_no_longer_exists_does_not_raise_exception_regression_116(
        self, jobstore
    ):
        # Test for regression https://github.com/jcass77/django-apscheduler/issues/116
        event = JobExecutionEvent(
            events.EVENT_JOB_EXECUTED, "finished_job", jobstore, timezone.now()
        )
        jobstore.handle_execution_event(event)

        assert not DjangoJobExecution.objects.filter(job_id=event.job_id).exists()

    @pytest.mark.django_db
    def test_handle_error_event_not_supported_raises_exception(self, jobstore):
        event = JobExecutionEvent(
            events.EVENT_ALL, "test_job", jobstore, timezone.now()
        )

        with pytest.raises(NotImplementedError):
            jobstore.handle_error_event(event)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "event_code",
        [
            events.EVENT_JOB_MISSED,
            events.EVENT_JOB_ERROR,
        ],
    )
    def test_handle_error_event_creates_job_execution(
        self, jobstore, create_add_job, event_code
    ):
        job = create_add_job(jobstore, dummy_job, datetime(2016, 5, 3))
        event = JobExecutionEvent(event_code, job.id, jobstore, timezone.now())
        jobstore.handle_error_event(event)

        assert DjangoJobExecution.objects.filter(job_id=event.job_id).exists()

    @pytest.mark.django_db
    def test_handle_error_event_no_exception_sets_exception_text(
        self, jobstore, create_add_job
    ):
        job = create_add_job(jobstore, dummy_job, datetime(2016, 5, 3))
        event = JobExecutionEvent(
            events.EVENT_JOB_ERROR, job.id, jobstore, timezone.now()
        )
        jobstore.handle_error_event(event)

        ex = DjangoJobExecution.objects.get(job_id=event.job_id)

        assert "raised an error!" in ex.exception

    @pytest.mark.django_db(transaction=True)
    def test_handle_error_event_for_job_that_no_longer_exists_does_not_raise_exception(
            self, jobstore
    ):
        event = JobExecutionEvent(
            events.EVENT_JOB_ERROR, "finished_job", jobstore, timezone.now()
        )
        jobstore.handle_error_event(event)

        assert not DjangoJobExecution.objects.filter(job_id=event.job_id).exists()

    @pytest.mark.django_db
    def test_register_event_listeners_registers_listeners(self, jobstore):
        jobstore.register_event_listeners()
        registered_event_codes = [event[1] for event in jobstore._scheduler._listeners]

        assert all(
            event_code in registered_event_codes
            for event_code in [
                events.EVENT_JOB_SUBMITTED | events.EVENT_JOB_MAX_INSTANCES,
                events.EVENT_JOB_EXECUTED,
                events.EVENT_JOB_ERROR | events.EVENT_JOB_MISSED,
            ]
        )


class TestDjangoJobStore:
    """
    We use the APScheduler tests to verify that DjangoJobStore implements the interface correctly.

    This test class should only contain tests that are specific to DjangoJobStore

    See 'test_apscheduler_jobstore.py' for details
    """

    @pytest.mark.django_db(transaction=True)
    def test_lookup_job_does_retry_on_db_operational_error(self, jobstore):
        with mock.patch.object(db.connection, "close") as close_mock:
            with pytest.raises(db.OperationalError, match="Some DB-related error"):
                with mock.patch(
                        "django_apscheduler.jobstores.DjangoJob.objects.get",
                        side_effect=conftest.raise_db_operational_error,
                ):
                    jobstore.lookup_job("some job")

            assert close_mock.call_count == 1

    @pytest.mark.django_db(transaction=True)
    def test_get_due_jobs_does_retry_on_db_operational_error(self, jobstore):
        with mock.patch.object(db.connection, "close") as close_mock:
            with pytest.raises(db.OperationalError, match="Some DB-related error"):
                with mock.patch(
                        "django_apscheduler.jobstores.DjangoJob.objects.filter",
                        side_effect=conftest.raise_db_operational_error,
                ):
                    jobstore.get_due_jobs(datetime(2016, 5, 3))

            assert close_mock.call_count == 1

    @pytest.mark.django_db(transaction=True)
    def test_get_next_run_time_does_retry_on_db_operational_error(self, jobstore):
        with mock.patch.object(db.connection, "close") as close_mock:
            with pytest.raises(db.OperationalError, match="Some DB-related error"):
                with mock.patch(
                        "django_apscheduler.jobstores.DjangoJob.objects.filter",
                        side_effect=conftest.raise_db_operational_error,
                ):
                    jobstore.get_next_run_time()

            assert close_mock.call_count == 1

    @pytest.mark.django_db(transaction=True)
    def test_add_job_does_retry_on_db_operational_error(self, jobstore, create_job):
        job = create_job(
            func=dummy_job,
            trigger="date",
            trigger_args={"run_date": datetime(2016, 5, 3)},
            id="test",
        )

        with mock.patch.object(db.connection, "close") as close_mock:
            with pytest.raises(db.OperationalError, match="Some DB-related error"):
                with mock.patch(
                        "django_apscheduler.jobstores.DjangoJob.objects.create",
                        side_effect=conftest.raise_db_operational_error,
                ):
                    jobstore.add_job(job)

            assert close_mock.call_count == 1

    @pytest.mark.django_db(transaction=True)
    def test_update_job_does_retry_on_db_operational_error(self, jobstore, create_job):
        job = create_job(
            func=dummy_job,
            trigger="date",
            trigger_args={"run_date": datetime(2016, 5, 3)},
            id="test",
        )

        with mock.patch.object(db.connection, "close") as close_mock:
            with pytest.raises(db.OperationalError, match="Some DB-related error"):
                with mock.patch(
                        "django_apscheduler.jobstores.DjangoJob.objects.select_for_update",
                        side_effect=conftest.raise_db_operational_error,
                ):
                    jobstore.update_job(job)

            assert close_mock.call_count == 1

    @pytest.mark.django_db(transaction=True)
    def test_remove_job_does_retry_on_db_operational_error(self, jobstore):
        with mock.patch.object(db.connection, "close") as close_mock:
            with pytest.raises(db.OperationalError, match="Some DB-related error"):
                with mock.patch(
                        "django_apscheduler.jobstores.DjangoJob.objects.select_for_update",
                        side_effect=conftest.raise_db_operational_error,
                ):
                    jobstore.remove_job("some job")

            assert close_mock.call_count == 1

    @pytest.mark.django_db(transaction=True)
    def test_remove_all_jobs_does_retry_on_db_operational_error(self, jobstore):
        with mock.patch.object(db.connection, "close") as close_mock:
            with pytest.raises(db.OperationalError, match="Some DB-related error"):
                with mock.patch(
                        "django_apscheduler.jobstores.DjangoJob.objects.all",
                        side_effect=conftest.raise_db_operational_error,
                ):
                    jobstore.remove_all_jobs()

            assert close_mock.call_count == 1

    @pytest.mark.django_db(transaction=True)
    def test_get_jobs_does_retry_on_db_operational_error(self, jobstore):
        with mock.patch.object(db.connection, "close") as close_mock:
            with pytest.raises(db.OperationalError, match="Some DB-related error"):
                with mock.patch(
                        "django_apscheduler.jobstores.DjangoJob.objects.filter",
                        side_effect=conftest.raise_db_operational_error,
                ):
                    jobstore._get_jobs()

            assert close_mock.call_count == 1


@pytest.mark.django_db
def test_register_events_raises_deprecation_warning(scheduler, jobstore):

    with warnings.catch_warnings(record=True) as w:

        register_events(scheduler, jobstore)
        assert len(w) == 1
        assert issubclass(w[-1].category, DeprecationWarning)
        assert "deprecated" in str(w[-1].message)


@pytest.mark.django_db
def test_register_job(scheduler, jobstore):
    register_job(scheduler, "interval", seconds=1)(dummy_job)
    scheduler.start()

    assert DjangoJob.objects.count() == 1


@pytest.mark.django_db
def test_register_job_raises_deprecation_warning(scheduler, jobstore):

    with warnings.catch_warnings(record=True) as w:

        register_job(scheduler, "interval", seconds=1)(dummy_job)
        assert len(w) == 1
        assert issubclass(w[-1].category, DeprecationWarning)
        assert "deprecated" in str(w[-1].message)
