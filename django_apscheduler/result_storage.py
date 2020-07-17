import logging
import time

from apscheduler.events import JobSubmissionEvent, JobExecutionEvent

from django_apscheduler.models import DjangoJobExecution, DjangoJob
from django_apscheduler.util import uct_datetime_to_datetime


class DjangoResultStorage:
    """
    Uses Django ORM table to store job status and results.

    You can override this class to change result storage.
    """

    logger = logging.getLogger("django_apscheduler.result_storage")

    def get_or_create_job_execution(
        self, job: DjangoJob, event: JobSubmissionEvent
    ) -> int:
        """
        Create and return new job execution item.

        :param job: DjangoJob instance
        :type job: django_apscheduler.models.DjangoJob
        :param event: JobSubmissionEvent instance
        :return: JobExecution id
        """
        # For blocking schedulers we first get `FINISH` event, and than `SUBMITTED` event
        job_execution = (
            DjangoJobExecution.objects.filter(
                job_id=job.id,
                run_time=uct_datetime_to_datetime(event.scheduled_run_times[0]),
            )
            .order_by("-id")
            .first()
        )

        if job_execution and job_execution.started is None:
            job_execution.started = time.time()
            try:
                job_execution.duration = float(job_execution.finished) - float(
                    job_execution.started
                )
            except TypeError:
                # Job is still running - ok.
                job_execution.duration = None

            job_execution.save()
            return job_execution.id

        return DjangoJobExecution.objects.create(
            job_id=job.id,
            status=DjangoJobExecution.SENT,
            started=time.time(),
            run_time=uct_datetime_to_datetime(event.scheduled_run_times[0]),
        ).id

    def register_job_executed(self, job: DjangoJob, event: JobExecutionEvent):
        """
        Registration of job execution status.

        :param job: DjangoJob instance
        :param event: JobExecutionEvent instance
        :return: JobExecution id
        """
        job_execution = (
            DjangoJobExecution.objects.filter(
                job_id=job.id,
                status=DjangoJobExecution.SENT,
                run_time=uct_datetime_to_datetime(event.scheduled_run_time),
            )
            .order_by("id")
            .last()
        )

        if not job_execution:
            job_execution = DjangoJobExecution.objects.create(
                job_id=job.id,
                status=DjangoJobExecution.SENT,
                run_time=uct_datetime_to_datetime(event.scheduled_run_time),
            )

        if job_execution.finished:
            self.logger.warning(f"Job already finished: {job_execution}.")
            return

        job_execution.finished = time.time()

        try:
            job_execution.duration = float(job_execution.finished) - float(
                job_execution.started
            )
        except TypeError:
            # TODO: Fix setting of `DjangoJob.started`
            # Job was never started?. This should probably be an error condition!
            job_execution.duration = None

        if event.exception:
            job_execution.exception = str(event.exception)
            job_execution.traceback = str(event.traceback)
            job_execution.status = DjangoJobExecution.ERROR
        else:
            job_execution.status = DjangoJobExecution.SUCCESS

        job_execution.save()
