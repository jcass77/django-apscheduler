import logging
from datetime import timedelta
from threading import RLock
from unittest import mock

import pytest
from apscheduler import events
from django import db
from django.utils import timezone

from django_apscheduler.models import DjangoJobExecution, DjangoJob
from tests import conftest

logging.basicConfig()


class TestDjangoJob:
    @pytest.mark.django_db
    def test_str(self, request):
        job = DjangoJob.objects.create(id="test_job", next_run_time=timezone.now())
        request.addfinalizer(job.delete)

        assert str(job).startswith("test_job (next run at:")

    @pytest.mark.django_db
    def test_str_paused(self, request):
        job = DjangoJob.objects.create(id="test_job")
        request.addfinalizer(job.delete)

        assert str(job) == "test_job (paused)"


class TestDjangoJobExecutionManager:
    @pytest.mark.django_db
    def test_delete_old_job_executions_deletes_old_jobs(
        self, request, jobstore, scheduler
    ):
        now = timezone.now()
        first_run = now - timedelta(seconds=10)
        second_run = now - timedelta(seconds=5)
        duration = 5.0

        job = DjangoJob.objects.create(id="test_job", next_run_time=now)
        request.addfinalizer(job.delete)

        DjangoJobExecution.objects.create(
            job=job,
            status=events.EVENT_JOB_EXECUTED,
            run_time=first_run,
            duration=duration,
            finished=(first_run + timedelta(seconds=duration)).timestamp(),
        )  # Old execution

        DjangoJobExecution.objects.create(
            job=job,
            status=events.EVENT_JOB_EXECUTED,
            run_time=second_run,
            duration=duration,
            finished=(first_run + timedelta(seconds=duration)).timestamp(),
        )  # Recent execution

        assert DjangoJobExecution.objects.count() == 2

        DjangoJobExecution.objects.delete_old_job_executions(duration + 1)

        assert DjangoJobExecution.objects.count() == 1


class TestDjangoJobExecution:
    @pytest.mark.django_db
    def test_atomic_update_or_create_creates_new_job(self, request, jobstore):
        now = timezone.now()
        job = DjangoJob.objects.create(id="test_job", next_run_time=now)
        request.addfinalizer(job.delete)

        DjangoJobExecution.atomic_update_or_create(
            RLock(),
            job.id,
            job.next_run_time - timedelta(seconds=5),
            DjangoJobExecution.SUCCESS,
        )

        assert DjangoJobExecution.objects.filter(job_id=job.id).exists()

    @pytest.mark.django_db
    def test_atomic_update_or_create_updates_existing_jobs(self, request, jobstore):
        now = timezone.now()
        job = DjangoJob.objects.create(id="test_job", next_run_time=now)
        request.addfinalizer(job.delete)

        ex = DjangoJobExecution.objects.create(
            job_id=job.id,
            run_time=job.next_run_time - timedelta(seconds=5),
            status=DjangoJobExecution.SENT,
        )

        assert ex.status == DjangoJobExecution.SENT
        assert ex.duration is None
        assert ex.finished is None

        DjangoJobExecution.atomic_update_or_create(
            RLock(),
            ex.job_id,
            ex.run_time,
            DjangoJobExecution.SUCCESS,
        )

        ex.refresh_from_db()

        assert ex.status == DjangoJobExecution.SUCCESS
        assert ex.duration is not None
        assert ex.finished is not None

    @pytest.mark.django_db
    def test_atomic_update_or_create_ignores_late_submission_events(
        self, request, jobstore
    ):
        now = timezone.now()
        job = DjangoJob.objects.create(id="test_job", next_run_time=now)
        request.addfinalizer(job.delete)

        ex = DjangoJobExecution.objects.create(
            job_id=job.id,
            run_time=job.next_run_time - timedelta(seconds=5),
            status=DjangoJobExecution.SUCCESS,
        )

        assert ex.status == DjangoJobExecution.SUCCESS
        assert ex.duration is None
        assert ex.finished is None

        DjangoJobExecution.atomic_update_or_create(
            RLock(),
            ex.job_id,
            ex.run_time,
            DjangoJobExecution.SENT,
        )

        ex.refresh_from_db()

        assert ex.status == DjangoJobExecution.SUCCESS
        assert ex.duration is None
        assert ex.finished is None

    @pytest.mark.django_db(transaction=True)
    def test_atomic_update_or_create_does_retry_on_db_operational_error(
            self, request, jobstore
    ):
        now = timezone.now()
        job = DjangoJob.objects.create(id="test_job", next_run_time=now)
        request.addfinalizer(job.delete)

        ex = DjangoJobExecution.objects.create(
            job_id=job.id,
            run_time=job.next_run_time - timedelta(seconds=5),
            status=DjangoJobExecution.SENT,
        )

        with mock.patch.object(db.connection, "close") as close_mock:
            with pytest.raises(db.OperationalError, match="Some DB-related error"):
                with mock.patch(
                        "django_apscheduler.models.DjangoJobExecution.objects.select_for_update",
                        side_effect=conftest.raise_db_operational_error,
                ):
                    DjangoJobExecution.atomic_update_or_create(
                        RLock(),
                        ex.job_id,
                        ex.run_time,
                        DjangoJobExecution.SUCCESS,
                    )

            assert close_mock.call_count == 1

    @pytest.mark.django_db
    def test_str(self, request):
        now = timezone.now()
        duration = 1
        prev_run = now - timedelta(seconds=5)

        job = DjangoJob.objects.create(id="test_job", next_run_time=now)
        request.addfinalizer(job.delete)

        ex = DjangoJobExecution.objects.create(
            job=job,
            status=DjangoJobExecution.SUCCESS,
            run_time=prev_run,
            duration=duration,
            finished=(prev_run + timedelta(duration)).timestamp(),
        )

        assert str(ex) == f"{ex.id}: job '{job.id}' ({DjangoJobExecution.SUCCESS})"
