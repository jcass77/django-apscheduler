# coding=utf-8
import time
from django.db import models
from django.utils.safestring import mark_safe


class DjangoJob(models.Model):
    name = models.CharField(max_length=255, unique=True)
    next_run_time = models.DateTimeField(db_index=True)
    # Perhaps consider using PickleField down the track.
    job_state = models.BinaryField()

    def __str__(self):
        status = 'next run at: %s' % self.next_run_time if self.next_run_time else 'paused'
        return '%s (%s)' % (self.name, status)

    class Meta:
        ordering = ('next_run_time', )

class DjangoJobExecution(models.Model):
    ADDED = u"Added"
    SENT = u"Started execution"
    MAX_INSTANCES = u"Max instances reached!"
    MISSED = u"Missed!"
    MODIFIED = u"Modified!"
    REMOVED = u"Removed!"
    ERROR = u"Error!"
    SUCCESS = u"Executed"

    job = models.ForeignKey(DjangoJob)
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

    args = models.CharField(max_length=1000)
    kwargs = models.CharField(max_length=1000)

    exception = models.CharField(max_length=1000, null=True)
    traceback = models.TextField(null=True)

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


