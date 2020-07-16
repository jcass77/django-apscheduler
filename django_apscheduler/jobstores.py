import logging
import pickle
import warnings
from typing import Union, List

from apscheduler.events import JobExecutionEvent, JobSubmissionEvent
from apscheduler.job import Job
from apscheduler.jobstores.base import BaseJobStore, JobLookupError
from apscheduler.schedulers.base import BaseScheduler

from django import db
from django.db import connections
from django.db.utils import OperationalError, ProgrammingError

from django_apscheduler.models import DjangoJob
from django_apscheduler.result_storage import DjangoResultStorage
from django_apscheduler.util import deserialize_dt, serialize_dt

logger = logging.getLogger("django_apscheduler")


# TODO: Remove this workaround, which seems to mute DB-related exceptions?
def ignore_database_error(on_error_value=None):
    def dec(func):
        from functools import wraps

        @wraps(func)
        def inner(*a, **k):
            try:
                return func(*a, **k)
            except (OperationalError, ProgrammingError) as e:
                warnings.warn(
                    f"Got OperationalError: {e}. Please, check that you have migrated the database via python "
                    f"manage.py migrate",
                    category=RuntimeWarning,
                    stacklevel=3,
                )
                return on_error_value
            finally:
                db.connections.close_all()

        return inner

    return dec


class DjangoJobStore(BaseJobStore):
    """
    Stores jobs in a Django database.

    :param int pickle_protocol: pickle protocol level to use (for serialization), defaults to the
           highest available
    """

    def __init__(self, pickle_protocol: int = pickle.HIGHEST_PROTOCOL):
        super().__init__()
        self.pickle_protocol = pickle_protocol

    @ignore_database_error()
    def lookup_job(self, job_id: str) -> Union[None, Job]:
        logger.debug(f"Lookup for job '{job_id}'...")
        try:
            job_state = DjangoJob.objects.get(name=job_id).job_state
            r = self._reconstitute_job(job_state) if job_state else None
            logger.debug(f"Found job: {r}")

            return r

        except DjangoJob.DoesNotExist:
            return None

    # TODO: Remove this (unused?) method?
    @ignore_database_error(on_error_value=[])
    def get_due_jobs(self, now) -> List[Job]:
        logger.debug(f"get_due_jobs for time={now}...")
        try:
            jobs = self._get_jobs(next_run_time__lte=serialize_dt(now))
            logger.debug(f"Found job: {jobs}")

            return jobs
        # TODO: Make this except clause more specific
        except Exception:
            logger.exception("Exception during 'get_due_jobs'")
            return []

    @ignore_database_error()
    def get_next_run_time(self):
        try:
            return deserialize_dt(
                DjangoJob.objects.filter(next_run_time__isnull=False)
                .earliest("next_run_time")
                .next_run_time
            )
        except DjangoJob.DoesNotExist:
            # No active jobs - OK
            pass

        # TODO: Make this except clause more specific
        except Exception:
            logger.exception("Exception during get_next_run_time for jobs")

        return None

    @ignore_database_error(on_error_value=[])
    def get_all_jobs(self):
        jobs = self._get_jobs()
        self._fix_paused_jobs_sorting(jobs)

        return jobs

    @ignore_database_error()
    def add_job(self, job: Job):
        db_job, created = DjangoJob.objects.get_or_create(
            defaults=dict(
                next_run_time=serialize_dt(job.next_run_time),
                job_state=pickle.dumps(job.__getstate__(), self.pickle_protocol),
            ),
            name=job.id,
        )

        if not created:
            logger.warning(
                f"Job with id '{job.id}' already in jobstore! I'll refresh it."
            )
            db_job.next_run_time = serialize_dt(job.next_run_time)
            db_job.job_state = pickle.dumps(job.__getstate__(), self.pickle_protocol)
            db_job.save()

    @ignore_database_error()
    def update_job(self, job: Job):
        updated = DjangoJob.objects.filter(name=job.id).update(
            next_run_time=serialize_dt(job.next_run_time),
            job_state=pickle.dumps(job.__getstate__(), self.pickle_protocol),
        )

        logger.debug(
            f"Update job '{job}': next_run_time={serialize_dt(job.next_run_time)}, job_state={job.__getstate__()}",
        )

        if updated == 0:
            logger.info(f"Job with id '{job.id}' not found")
            raise JobLookupError(job.id)

    @ignore_database_error()
    def remove_job(self, job_id: str):
        _, num_deleted = DjangoJob.objects.filter(name=job_id).delete()
        if num_deleted == 0:
            logger.warning(f"Job with id '{job_id}' not found. Cannot remove job.")

    @ignore_database_error()
    def remove_all_jobs(self):
        # TODO: Replace raw SQL below with Django ORM equivalents?
        with connections["default"].cursor() as c:
            c.execute(
                """
                DELETE FROM django_apscheduler_djangojobexecution;
            """
            )
            c.execute("DELETE FROM django_apscheduler_djangojob;")

    def _reconstitute_job(self, job_state):
        job_state = pickle.loads(job_state)
        job_state["jobstore"] = self

        job = Job.__new__(Job)
        job.__setstate__(job_state)
        job._scheduler = self._scheduler
        job._jobstore_alias = self._alias

        return job

    def _get_jobs(self, **filters):
        job_states = DjangoJob.objects.filter(**filters).values_list("id", "job_state")
        jobs = []
        failed_job_ids = set()

        for job_id, job_state in job_states:
            try:
                jobs.append(self._reconstitute_job(job_state))
            # TODO: Make this except clause more specific
            except Exception:
                self._logger.exception(
                    f"Unable to restore job '{job_id}'. Removing it..."
                )
                failed_job_ids.add(job_id)

        # Remove all the jobs we failed to restore
        if failed_job_ids:
            logger.warning(f"Removing bad jobs: {failed_job_ids}")
            DjangoJob.objects.filter(id__in=failed_job_ids).delete()

        def map_jobs(job):
            job.next_run_time = deserialize_dt(job.next_run_time)
            return job

        return list(map(map_jobs, jobs))


class _EventManager:

    logger = logger.getChild("events")

    def __init__(self, storage=None):
        self.storage = storage or DjangoResultStorage()

    def __call__(self, event: JobSubmissionEvent):
        logger.debug(f"Received event: {event}, {type(event)}, {event.__dict__}")
        try:
            if isinstance(event, JobSubmissionEvent):
                self._process_submission_event(event)

            elif isinstance(event, JobExecutionEvent):
                self._process_execution_event(event)

        except Exception as e:
            self.logger.exception(str(e))

    @ignore_database_error()
    def _process_submission_event(self, event: JobSubmissionEvent):
        try:
            job = DjangoJob.objects.get(name=event.job_id)
        except DjangoJob.DoesNotExist:
            self.logger.warning(f"Job with id '{event.job_id}' not found in database!")
            return

        self.storage.get_or_create_job_execution(job, event)

    @ignore_database_error()
    def _process_execution_event(self, event: JobExecutionEvent):

        try:
            job = DjangoJob.objects.get(name=event.job_id)
        except DjangoJob.DoesNotExist:
            self.logger.warning(f"Job with id '{event.job_id}' not found in database")
            return

        self.storage.register_job_executed(job, event)


def register_events(scheduler, result_storage=None):
    scheduler.add_listener(_EventManager(result_storage))


def register_job(scheduler: BaseScheduler, *a, **k) -> callable:
    """
    Helper decorator for job registration.

    Automatically fills id parameter to prevent jobs duplication.
    See this comment for explanation: https://github.com/jarekwg/django-apscheduler/pull/9#issuecomment-342074372

    Usage example::

        @register_job(scheduler, "interval", seconds=1)
        def test_job():
            time.sleep(4)
            print("I'm a test job!")

    :param scheduler: Scheduler instance
    :type scheduler: BaseScheduler

    :param a, k: Params, will be passed to scheduler.add_job method. See :func:`BaseScheduler.add_job`
    """

    def inner(func):
        k.setdefault("id", f"{func.__module__}.{func.__name__}")
        scheduler.add_job(func, *a, **k)

        return func

    return inner
