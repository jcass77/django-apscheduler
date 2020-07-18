import random
import time

from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings

from django_apscheduler.jobstores import DjangoJobStore, register_job

scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
scheduler.add_jobstore(DjangoJobStore(), "default")


@register_job(scheduler, "interval", seconds=5, replace_existing=True)
def test_job():
    time.sleep(random.randrange(1, 100, 1) / 100.0)
    print("I'm a test job!")
    # raise ValueError("Olala!")


scheduler.start()
print("Scheduler started!")
