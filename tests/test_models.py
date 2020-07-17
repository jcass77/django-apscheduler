import datetime
import logging

from apscheduler.events import JobExecutionEvent, JobSubmissionEvent
from django.utils import timezone

from django_apscheduler.jobstores import register_events
from django_apscheduler.models import DjangoJobExecution

logging.basicConfig()


class TestDjangoJobExecutionManager:
    def test_delete_old_job_executions_deletes_old_jobs(self, db, job, scheduler):
        register_events(scheduler)
        scheduler.add_job(job, trigger="interval", seconds=1, id="job_1")
        scheduler.add_job(job, trigger="interval", seconds=1, id="job_2")

        scheduler.start()

        now = timezone.now()
        one_second_ago = now - datetime.timedelta(seconds=1)  # Simulate

        scheduler._dispatch_event(
            JobSubmissionEvent(32768, "job_1", None, [one_second_ago])
        )

        scheduler._dispatch_event(
            JobExecutionEvent(4096, "job_1", None, one_second_ago)
        )

        scheduler._dispatch_event(JobSubmissionEvent(32768, "job_2", None, [now]))
        scheduler._dispatch_event(JobExecutionEvent(4096, "job_2", None, now))

        assert DjangoJobExecution.objects.count() == 2

        DjangoJobExecution.objects.delete_old_job_executions(1)

        assert DjangoJobExecution.objects.count() == 1
