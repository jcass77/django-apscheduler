from datetime import timedelta

import pytest
from django.utils import timezone

from django_apscheduler.admin import DjangoJobAdmin, DjangoJobExecutionAdmin
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
    def test_average_duration_no_executions_shows_none_text(self, request):
        now = timezone.now()
        run_time = now - timedelta(seconds=60)

        job = DjangoJob.objects.create(id="test_job", next_run_time=run_time)
        request.addfinalizer(job.delete)

        admin = DjangoJobAdmin(DjangoJob, None)
        admin.get_queryset(request)

        assert admin.average_duration(job) == "None"


class TestDjangoJobExecutionAdmin:
    @pytest.mark.django_db
    def test_html_status_returns_colored_status_text(self, rf, request):
        now = timezone.now()

        job = DjangoJob.objects.create(id="test_job", next_run_time=now)
        request.addfinalizer(job.delete)

        execution = DjangoJobExecution.objects.create(
            job=job, status=DjangoJobExecution.SUCCESS, run_time=now,
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
            job=job, status=DjangoJobExecution.SUCCESS, run_time=now,
        )

        admin = DjangoJobExecutionAdmin(DjangoJob, None)
        admin.get_queryset(rf.get("/admin/django_apscheduler/djangojob"))

        assert admin.duration_text(execution) == "N/A"
