from datetime import timedelta
from unittest import mock

import pytest
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.contrib.messages.storage.base import BaseStorage
from django.utils import timezone
from django.utils.html import format_html

from django_apscheduler.admin import DjangoJobAdmin, DjangoJobExecutionAdmin
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJob, DjangoJobExecution


class TestDjangoJobAdmin:
    @pytest.mark.django_db
    def test_get_queryset_calculates_averages(self, rf, request):
        now = timezone.now()
        run_time = now - timedelta(seconds=60)

        job = DjangoJob.objects.create(id="test_job", next_run_time=run_time)
        request.addfinalizer(job.delete)

        DjangoJobExecution.objects.create(
            job=job,
            status=DjangoJobExecution.SUCCESS,
            run_time=run_time - timedelta(seconds=60),
            duration=5,
            finished=(run_time + timedelta(seconds=5)).timestamp(),
        )  # Old job execution

        DjangoJobExecution.objects.create(
            job=job,
            status=DjangoJobExecution.SUCCESS,
            run_time=run_time,
            duration=10,
            finished=(run_time + timedelta(seconds=10)).timestamp(),
        )  # Most recent job execution

        admin = DjangoJobAdmin(DjangoJob, None)
        admin.get_queryset(rf.get("/admin/django_apscheduler/djangojob"))

        assert admin.avg_duration_qs.count() == 1
        assert admin.avg_duration_qs.first()[0] == job.id
        assert admin.avg_duration_qs.first()[1] == 7.5

    @pytest.mark.django_db
    def test_local_run_time_returns_paused_if_no_run_time_scheduled(self, rf, request):
        job = DjangoJob.objects.create(id="test_job")
        request.addfinalizer(job.delete)

        admin = DjangoJobAdmin(DjangoJob, None)
        admin.get_queryset(rf.get("/admin/django_apscheduler/djangojob"))

        assert admin.local_run_time(job) == "(paused)"

    @pytest.mark.django_db
    def test_average_duration_returns_correct_value(self, rf, request):
        now = timezone.now()
        run_time = now - timedelta(seconds=60)

        job = DjangoJob.objects.create(id="test_job", next_run_time=run_time)
        request.addfinalizer(job.delete)

        DjangoJobExecution.objects.create(
            job=job,
            status=DjangoJobExecution.SUCCESS,
            run_time=run_time - timedelta(seconds=60),
            duration=5,
            finished=(run_time + timedelta(seconds=5)).timestamp(),
        )  # Old job execution

        DjangoJobExecution.objects.create(
            job=job,
            status=DjangoJobExecution.SUCCESS,
            run_time=run_time,
            duration=10,
            finished=(run_time + timedelta(seconds=10)).timestamp(),
        )  # Most recent job execution

        admin = DjangoJobAdmin(DjangoJob, None)
        admin.get_queryset(rf.get("/admin/django_apscheduler/djangojob"))

        assert admin.average_duration(job) == 7.5

    @pytest.mark.django_db
    def test_average_duration_no_executions_shows_none_text(self, request, rf):
        now = timezone.now()
        run_time = now - timedelta(seconds=60)

        job = DjangoJob.objects.create(id="test_job", next_run_time=run_time)
        request.addfinalizer(job.delete)

        admin = DjangoJobAdmin(DjangoJob, None)
        r = rf.get("/django_apscheduler/djangojob/")
        admin.get_queryset(r)

        assert admin.average_duration(job) == "None"

    @pytest.mark.django_db(transaction=True)
    def test_run_selected_jobs_creates_job_execution_entry(self, rf, monkeypatch):
        monkeypatch.setattr(
            settings, "APSCHEDULER_RUN_NOW_TIMEOUT", 1
        )  # Shorten timeout to reduce test runtime

        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore())
        scheduler.start()

        job = scheduler.add_job(print, trigger="interval", seconds=60)

        admin = DjangoJobAdmin(DjangoJob, None)

        r = rf.get("/django_apscheduler/djangojob/")
        # Add support for Django messaging framework
        r._messages = mock.MagicMock(BaseStorage)
        r._messages.add = mock.MagicMock()

        assert not DjangoJobExecution.objects.filter(job_id=job.id).exists()

        admin.run_selected_jobs(r, DjangoJob.objects.filter(id=job.id))

        assert DjangoJobExecution.objects.filter(job_id=job.id).exists()
        r._messages.add.assert_called_with(20, f"Executed job '{job.id}'!", "")

        scheduler.shutdown()

    @pytest.mark.django_db(transaction=True)
    def test_run_selected_jobs_job_not_found_skips_execution(self, rf):
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore())
        scheduler.start()

        job = DjangoJob.objects.create(id="test_job")

        admin = DjangoJobAdmin(DjangoJob, None)

        r = rf.get("/django_apscheduler/djangojob/")
        # Add support for Django messaging framework
        r._messages = mock.MagicMock(BaseStorage)
        r._messages.add = mock.MagicMock()

        admin.run_selected_jobs(r, DjangoJob.objects.filter(id=job.id))

        assert DjangoJobExecution.objects.count() == 0
        r._messages.add.assert_called_with(
            30, "Could not find job test_job in the database! Skipping execution...", ""
        )

        scheduler.shutdown()

    @pytest.mark.django_db(transaction=True)
    def test_run_selected_jobs_enforces_timeout(self, rf, monkeypatch):
        monkeypatch.setattr(
            settings, "APSCHEDULER_RUN_NOW_TIMEOUT", 1
        )  # Shorten timeout to reduce test runtime

        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore())
        scheduler.start()

        job = scheduler.add_job(print, trigger="interval", seconds=60)

        admin = DjangoJobAdmin(DjangoJob, None)

        r = rf.get("/django_apscheduler/djangojob/")
        # Add support for Django messaging framework
        r._messages = mock.MagicMock(BaseStorage)
        r._messages.add = mock.MagicMock()

        with mock.patch("django_apscheduler.admin.BackgroundScheduler.add_listener"):
            admin.run_selected_jobs(r, DjangoJob.objects.filter(id=job.id))

        assert DjangoJobExecution.objects.count() == 0
        r._messages.add.assert_called_with(
            40,
            format_html(
                "Maximum runtime of {} seconds exceeded! Not all jobs could be completed successfully. "
                "Pending jobs: {}",
                admin._job_execution_timeout,
                ",".join({job.id}),
            ),
            "",
        )

        scheduler.shutdown()


class TestDjangoJobExecutionAdmin:
    @pytest.mark.django_db
    def test_html_status_returns_colored_status_text(self, rf, request):
        now = timezone.now()

        job = DjangoJob.objects.create(id="test_job", next_run_time=now)
        request.addfinalizer(job.delete)

        execution = DjangoJobExecution.objects.create(
            job=job,
            status=DjangoJobExecution.SUCCESS,
            run_time=now,
        )

        admin = DjangoJobExecutionAdmin(DjangoJob, None)
        admin.get_queryset(rf.get("/admin/django_apscheduler/djangojob"))

        assert "green" in admin.html_status(execution)

    @pytest.mark.django_db
    def test_duration_text_no_duration_returns_na(self, rf, request):
        now = timezone.now()

        job = DjangoJob.objects.create(id="test_job", next_run_time=now)
        request.addfinalizer(job.delete)

        execution = DjangoJobExecution.objects.create(
            job=job,
            status=DjangoJobExecution.SUCCESS,
            run_time=now,
        )

        admin = DjangoJobExecutionAdmin(DjangoJob, None)
        admin.get_queryset(rf.get("/admin/django_apscheduler/djangojob"))

        assert admin.duration_text(execution) == "N/A"
