import logging
import time

from django_apscheduler.models import DjangoJobExecution
from django_apscheduler.util import serialize_dt


class DjangoResultStorage(object):
    """
    Uses Django ORM table for store job status and results.
    You can override this class to change result storage.
    """
    LOGGER = logging.getLogger("django_apscheduler.result_storage")

    def get_or_create_job_execution(self, job, event):
        """
        Create and return new job execution item.
        :param job: DjangoJob instance
        :type job: django_apscheduler.models.DjangoJob
        :param event: JobSubmissionEvent instance
        :return: JobExecution id
        """
        # type: (DjangoJob, JobSubmissionEvent)->int

        # For blocking schedulers we first got FINISH event, and than - SUBMITTED event
        job_execution = DjangoJobExecution.objects.filter(
            job=job,
            run_time=serialize_dt(event.scheduled_run_times[0])
        ).order_by("-id").first()

        if job_execution and job_execution.started is None:
            job_execution.started = time.time()
            try:
                job_execution.duration = float(job_execution.finished) - float(job_execution.started)
            except:
                job_execution.duration = None

            job_execution.save()
            return job_execution.id

        return DjangoJobExecution.objects.create(
            job=job,
            status=DjangoJobExecution.SENT,
            started=time.time(),
            run_time=serialize_dt(event.scheduled_run_times[0])
        ).id

    def register_job_executed(self, job, event):
        """
        Registration of job execution status
        :param job: DjangoJob instance
        :param event: JobExecutionEvent instance
        :return: JobExecution id
        """
        # type: (DjangoJobExecution, JobExecutionEvent)->int

        job_execution = DjangoJobExecution.objects.filter(
            job=job,
            status=DjangoJobExecution.SENT,
            run_time=serialize_dt(event.scheduled_run_time)
        ).order_by("id").last()  # type: DjangoJobExecution

        if not job_execution:
            job_execution = DjangoJobExecution.objects.create(
                job=job,
                status=DjangoJobExecution.SENT,
                run_time=serialize_dt(event.scheduled_run_time)
            )

        if job_execution.finished:
            self.LOGGER.warning("Job already finished! %s", job_execution)
            return

        job_execution.finished = time.time()

        try:
            job_execution.duration = float(job_execution.finished) - float(job_execution.started)
        except:
            job_execution.duration = 0

        job_execution.status = DjangoJobExecution.SUCCESS

        if event.exception:
            job_execution.exception = str(event.exception)
            job_execution.traceback = str(event.traceback)
            job_execution.status = DjangoJobExecution.ERROR

        job_execution.save()
