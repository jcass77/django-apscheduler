from django.db import models


class DjangoJob(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    next_run_time = models.DateTimeField(db_index=True)
    # Perhaps consider using PickleField down the track.
    job_state = models.BinaryField()

    class Meta:
        ordering = ('next_run_time', )
