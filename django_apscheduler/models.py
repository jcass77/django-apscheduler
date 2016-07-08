from django.db import models


class DjangoJob(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    next_run_time = models.DateTimeField(db_index=True)
    # Perhaps consider using PickleField down the track.
    job_state = models.BinaryField()

    def __str__(self):
        status = 'next run at: %s' % self.next_run_time if self.next_run_time else 'paused'
        return '%s (%s)' % (self.id, status)

    class Meta:
        ordering = ('next_run_time', )
