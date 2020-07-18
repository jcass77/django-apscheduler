import datetime
import logging

from apscheduler import events
from apscheduler.events import JobExecutionEvent, JobSubmissionEvent
from django.utils import timezone

from django_apscheduler.models import DjangoJobExecution

logging.basicConfig()


class TestDjangoJobExecutionManager:
    def test_delete_old_job_executions_deletes_old_jobs(
        self, db, djangojobstore, scheduler, job
    ):
        scheduler.add_job(job, trigger="interval", seconds=1, id="job_1")
        scheduler.add_job(job, trigger="interval", seconds=1, id="job_2")

        scheduler.start()

        now = timezone.now()
        one_second_ago = now - datetime.timedelta(seconds=1)  # Simulate

        scheduler._dispatch_event(
            JobSubmissionEvent(
                events.EVENT_JOB_SUBMITTED, "job_1", djangojobstore, [one_second_ago],
            )
        )

        scheduler._dispatch_event(
            JobExecutionEvent(
                events.EVENT_JOB_EXECUTED, "job_1", djangojobstore, one_second_ago
            )
        )

        scheduler._dispatch_event(
            JobSubmissionEvent(
                events.EVENT_JOB_SUBMITTED, "job_2", djangojobstore, [now]
            )
        )
        scheduler._dispatch_event(
            JobExecutionEvent(events.EVENT_JOB_EXECUTED, "job_2", djangojobstore, now)
        )

        assert DjangoJobExecution.objects.count() == 2

        DjangoJobExecution.objects.delete_old_job_executions(1)

        assert DjangoJobExecution.objects.count() == 1
