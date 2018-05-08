import logging
import pickle
import warnings

from apscheduler import events
from apscheduler.events import JobExecutionEvent, JobSubmissionEvent
from apscheduler.job import Job
from apscheduler.jobstores.base import BaseJobStore, ConflictingIdError, JobLookupError
from apscheduler.schedulers.base import BaseScheduler

from django.core.exceptions import ObjectDoesNotExist
from django.db import connections
from django.db.utils import OperationalError, ProgrammingError

from django_apscheduler.models import DjangoJob
from django_apscheduler.result_storage import DjangoResultStorage
from django_apscheduler.util import deserialize_dt, serialize_dt

LOGGER = logging.getLogger("django_apscheduler")

def ignore_database_error(on_error_value=None):

    def dec(func):
        from functools import wraps

        @wraps(func)
        def inner(*a, **k):
            try:
                return func(*a, **k)
            except (OperationalError, ProgrammingError) as e:
                warnings.warn(
                    "Got OperationalError: {}. "
                    "Please, check that you have migrated the database via python manage.py migrate".format(e),
                    category=RuntimeWarning,
                    stacklevel=3
                )
                return on_error_value
        return inner
    return dec


class DjangoJobStore(BaseJobStore):
    """
    Stores jobs in a Django database.
    :param int pickle_protocol: pickle protocol level to use (for serialization), defaults to the
        highest available
    """

    def __init__(self, pickle_protocol=pickle.HIGHEST_PROTOCOL):
        super(DjangoJobStore, self).__init__()
        self.pickle_protocol = pickle_protocol

    @ignore_database_error()
    def lookup_job(self, job_id):
        LOGGER.debug("Lookup for a job %s", job_id)
        try:
            job_state = DjangoJob.objects.get(name=job_id).job_state
        except DjangoJob.DoesNotExist:
            return None
        r = self._reconstitute_job(job_state) if job_state else None
        LOGGER.debug("Got %s", r)
        return r

    @ignore_database_error(on_error_value=[])
    def get_due_jobs(self, now):
        LOGGER.debug("get_due_jobs for time=%s", now)
        try:
            out = self._get_jobs(next_run_time__lte=serialize_dt(now))
            LOGGER.debug("Got %s", out)
            return out
        except:
            LOGGER.exception("Exception during getting jobs")
            return []


    @ignore_database_error()
    def get_next_run_time(self):
        try:
            return deserialize_dt(DjangoJob.objects.first().next_run_time)
        except AttributeError:  # no active jobs
            return None

    @ignore_database_error(on_error_value=[])
    def get_all_jobs(self):
        jobs = self._get_jobs()
        self._fix_paused_jobs_sorting(jobs)
        return jobs

    @ignore_database_error()
    def add_job(self, job):
        dbJob, created = DjangoJob.objects.get_or_create(
            defaults=dict(
                next_run_time=serialize_dt(job.next_run_time),
                job_state=pickle.dumps(job.__getstate__(), self.pickle_protocol)
            ),
            name=job.id,
        )

        if not created:
            LOGGER.warning("Job with id %s already in jobstore. I'll refresh it", job.id)
            dbJob.next_run_time = serialize_dt(job.next_run_time)
            dbJob.job_state=pickle.dumps(job.__getstate__(), self.pickle_protocol)
            dbJob.save()

    @ignore_database_error()
    def update_job(self, job):
        updated = DjangoJob.objects.filter(name=job.id).update(
            next_run_time=serialize_dt(job.next_run_time),
            job_state=pickle.dumps(job.__getstate__(), self.pickle_protocol)
        )

        LOGGER.debug(
            "Update job %s: next_run_time=%s, job_state=%s",
            job,
            serialize_dt(job.next_run_time),
            job.__getstate__()

        )

        if updated == 0:
            LOGGER.info("Job with id %s not found", job.id)
            raise JobLookupError(job.id)

    @ignore_database_error()
    def remove_job(self, job_id):
        qs = DjangoJob.objects.filter(name=job_id)
        if not qs.exists():
            LOGGER.warning("Job with id %s not found. Can't remove job.", job_id)
        qs.delete()

    @ignore_database_error()
    def remove_all_jobs(self):
        with connections["default"].cursor() as c:
            c.execute("""
                DELETE FROM django_apscheduler_djangojobexecution;
            """)
            c.execute("DELETE FROM django_apscheduler_djangojob;")

    def _reconstitute_job(self, job_state):
        job_state = pickle.loads(job_state)
        job_state['jobstore'] = self
        job = Job.__new__(Job)
        job.__setstate__(job_state)
        job._scheduler = self._scheduler
        job._jobstore_alias = self._alias
        return job

    def _get_jobs(self, **filters):
        job_states = DjangoJob.objects.filter(**filters).values_list('id', 'job_state')
        jobs = []
        failed_job_ids = set()
        for job_id, job_state in job_states:
            try:
                jobs.append(self._reconstitute_job(job_state))
            except:
                self._logger.exception('Unable to restore job "%s" -- removing it', job_id)
                failed_job_ids.add(job_id)

        # Remove all the jobs we failed to restore
        DjangoJob.objects.filter(name__in=failed_job_ids).delete()

        def map_jobs(job):
            job.next_run_time = deserialize_dt(job.next_run_time)
            return job

        return list(map(map_jobs, jobs))


def event_name(code):
    for key in dir(events):
        if getattr(events, key) == code:
            return key


class _EventManager(object):

    LOGGER = LOGGER.getChild("events")

    def __init__(self, storage=None):
        self.storage = storage or DjangoResultStorage()

    def __call__(self, event):
        LOGGER.debug("Got event: %s, %s, %s",
                      event, type(event), event.__dict__)
        # print event, type(event), event.__dict__
        try:
            if isinstance(event, JobSubmissionEvent):
                self._process_submission_event(event)
            elif isinstance(event, JobExecutionEvent):
                self._process_execution_event(event)
        except Exception as e:
            self.LOGGER.exception(str(e))

    def _process_submission_event(self, event):
        # type: (JobSubmissionEvent)->None

        try:
            job = DjangoJob.objects.get(name=event.job_id)
        except ObjectDoesNotExist:
            self.LOGGER.warning("Job with id %s not found in database", event.job_id)
            return

        self.storage.get_or_create_job_execution(job, event)

    def _process_execution_event(self, event):
        # type: (JobExecutionEvent)->None

        try:
            job = DjangoJob.objects.get(name=event.job_id)
        except ObjectDoesNotExist:
            self.LOGGER.warning("Job with id %s not found in database", event.job_id)
            return

        self.storage.register_job_executed(job, event)


def register_events(scheduler, result_storage=None):
    scheduler.add_listener(_EventManager(result_storage))


def register_job(scheduler, *a, **k):
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
    # type: (BaseScheduler)->callable

    def inner(func):
        k.setdefault("id", "{}.{}".format(func.__module__, func.__name__))
        scheduler.add_job(func, *a, **k)
        return func

    return inner
