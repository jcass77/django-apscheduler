# coding=utf-8
from datetime import timedelta

from django.db import models, connection
from django.utils.safestring import mark_safe
from django.utils.timezone import now
import time
import logging

LOGGER = logging.getLogger("django_apscheduler")


class DjangoJobManager(models.Manager):
    """
    This manager pings database each request after 30s IDLE to prevent MysqlGoneAway error
    """
    _last_ping = 0
    _ping_interval = 30

    def get_queryset(self):
        self.__ping()
        return super(DjangoJobManager, self).get_queryset()

    def __ping(self):
        if time.time() - self._last_ping < self._ping_interval:
            return

        try:
            with connection.cursor() as c:
                c.execute("SELECT 1")
        except Exception as e:
            self.__reconnect()

        self._last_ping = time.time()

    def __reconnect(self):
        LOGGER.warning("Mysql closed the connection. Perform reconnect...")

        if connection.connection:
            connection.connection.close()
            connection.connection = None
        else:
            LOGGER.warning("Connection was already closed.")


class DjangoJob(models.Model):
    name = models.CharField(max_length=255, unique=True)  # id of job
    next_run_time = models.DateTimeField(db_index=True, blank=True, null=True)
    # Perhaps consider using PickleField down the track.
    job_state = models.BinaryField()

    objects = DjangoJobManager()

    def __str__(self):
        status = 'next run at: %s' % self.next_run_time if self.next_run_time else 'paused'
        return '%s (%s)' % (self.name, status)

    class Meta:
        ordering = ('next_run_time', )


class DjangoJobExecutionManager(models.Manager):
    def delete_old_job_executions(self, max_age):
        """
        Delete old job executions from the database.

        :param max_age: The maximum age (in seconds). Executions that are older
        than this will be deleted.
        """
        self.filter(
            run_time__lte=now() - timedelta(seconds=max_age),
        ).delete()


class DjangoJobExecution(models.Model):
    ADDED = u"Added"
    SENT = u"Started execution"
    MAX_INSTANCES = u"Max instances reached!"
    MISSED = u"Missed!"
    MODIFIED = u"Modified!"
    REMOVED = u"Removed!"
    ERROR = u"Error!"
    SUCCESS = u"Executed"

    job = models.ForeignKey(DjangoJob, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=[
        [x, x]
        for x in [ADDED, SENT, MAX_INSTANCES, MISSED, MODIFIED,
                  REMOVED, ERROR, SUCCESS]
    ])
    run_time = models.DateTimeField(db_index=True)
    duration = models.DecimalField(max_digits=15, decimal_places=2,
                                   default=None, null=True)

    started = models.DecimalField(max_digits=15, decimal_places=2,
                                  default=None, null=True)
    finished = models.DecimalField(max_digits=15, decimal_places=2,
                                   default=None, null=True)

    exception = models.CharField(max_length=1000, null=True)
    traceback = models.TextField(null=True)

    objects = DjangoJobExecutionManager()

    def html_status(self):
        m = {
            self.ADDED: "RoyalBlue",
            self.SENT: "SkyBlue",
            self.MAX_INSTANCES: "yellow",
            self.MISSED: "yellow",
            self.MODIFIED: "yellow",
            self.REMOVED: "red",
            self.ERROR: "red",
            self.SUCCESS: "green"
        }

        return mark_safe("<p style=\"color: {}\">{}</p>".format(
            m[self.status],
            self.status
        ))

    def __unicode__(self):
        return "Execution id={}, status={}, job={}".format(
            self.id, self.status, self.job
        )

    class Meta:
        ordering = ('-run_time', )
