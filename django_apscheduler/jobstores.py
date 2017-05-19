import logging
import pickle

import time

from apscheduler.events import JobExecutionEvent
from apscheduler.executors.base import BaseExecutor
from apscheduler.job import Job
from apscheduler.jobstores.base import BaseJobStore, ConflictingIdError, JobLookupError

from django.db import IntegrityError, connections
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from django_apscheduler.models import DjangoJobExecution
from util import serialize_dt, deserialize_dt
from .models import DjangoJob


class DjangoJobStore(BaseJobStore):
    """
    Stores jobs in a Django database.
    :param int pickle_protocol: pickle protocol level to use (for serialization), defaults to the
        highest available
    """

    def __init__(self, pickle_protocol=pickle.HIGHEST_PROTOCOL):
        super(DjangoJobStore, self).__init__()
        self.pickle_protocol = pickle_protocol

    def lookup_job(self, job_id):
        try:
            job_state = DjangoJob.objects.get(name=job_id).job_state
        except DjangoJob.DoesNotExist:
            return None
        return self._reconstitute_job(job_state) if job_state else None

    def get_due_jobs(self, now):
        try:
            return self._get_jobs(next_run_time__lte=serialize_dt(now))
        except:
            logging.exception("")


    def get_next_run_time(self):
        try:
            return deserialize_dt(DjangoJob.objects.first().next_run_time)
        except AttributeError:  # no active jobs
            return None

    def get_all_jobs(self):
        jobs = self._get_jobs()
        self._fix_paused_jobs_sorting(jobs)
        return jobs

    def add_job(self, job):
        if DjangoJob.objects.filter(
            name=job.id
        ).exists():
            raise ConflictingIdError(job.id)

        DjangoJob.objects.create(
            name=job.id,
            next_run_time=serialize_dt(job.next_run_time),
            job_state=pickle.dumps(job.__getstate__(), self.pickle_protocol)
        )

    def update_job(self, job):
        updated = DjangoJob.objects.filter(name=job.id).update(
            next_run_time=serialize_dt(job.next_run_time),
            job_state=pickle.dumps(job.__getstate__(), self.pickle_protocol)
        )
        if updated == 0:
            raise JobLookupError(job.id)

    def remove_job(self, job_id):
        deleted, _ = DjangoJob.objects.filter(name=job_id).delete()
        if deleted == 0:
            raise JobLookupError(job_id)

    def remove_all_jobs(self):
        with connections["default"].cursor() as c:
            c.execute("""
            DELETE FROM django_apscheduler_djangojobexecution;
            DELETE FROM django_apscheduler_djangojob
            """)

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

        return map(map_jobs, jobs)


from apscheduler import events

def event_name(code):
    for key in dir(events):
        if getattr(events, key) == code:
            return key

class WrapExecutor(object):

    def __init__(self, executor):
        ":type executor: BaseExecutor"
        self.executor = executor

        self._orig_do_submit_job = self.executor._do_submit_job
        self._orig_run_job_success = self.executor._run_job_success
        self._orig_run_job_error = self.executor._run_job_error

        self.executor._do_submit_job = self._do_submit_job
        self.executor._run_job_success = self._run_job_success
        self.executor._run_job_error = self._run_job_error

    def __getattr__(self, item):
        return getattr(self.executor, item)


    def _do_submit_job(self, job, run_times):
        ":type job: Job"

        dbJob = DjangoJob.objects.get(name=job.id)
        DjangoJobExecution.objects.create(
            status=DjangoJobExecution.SENT,
            args=repr(job.args),
            kwargs=repr(job.kwargs),
            started=time.time(),
            job=dbJob,
            run_time=serialize_dt(job.next_run_time)
        )

        return self._orig_do_submit_job(job, run_times)

    def _get_execution(self, job_id):
        return DjangoJobExecution.objects.filter(
            job__name=job_id
        ).first()

    def _run_job_success(self, job_id, events):
        try:
            event = events[0]   #type: JobExecutionEvent
        except:
            event = None

        dje = self._get_execution(job_id)
        dje.finished = time.time()
        dje.duration = dje.finished - float(dje.started)

        if event and event.exception:
            dje.status = DjangoJobExecution.ERROR
            dje.exception = event.exception
            dje.traceback = event.traceback
        else:
            dje.status = DjangoJobExecution.SUCCESS
        dje.save()

        return self._orig_run_job_success(job_id, events)

    def _run_job_error(self, job_id, exc, traceback=None):
        dje = self._get_execution(job_id)

        dje.status = DjangoJobExecution.ERROR
        dje.exception = exc
        dje.traceback = traceback
        dje.save()

        return self._orig_run_job_error(job_id, exc, traceback)

def register_events(scheduler):
    """
    :type scheduler: apscheduler.schedulers.base.BaseScheduler
    """


    for key, value in scheduler._executors.items():
        scheduler._executors[key] = WrapExecutor(value)