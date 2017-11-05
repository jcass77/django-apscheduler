import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

from django_apscheduler.jobstores import DjangoJobStore, _EventManager, register_events

import logging
logging.basicConfig()


scheduler = BackgroundScheduler()

scheduler.add_jobstore(DjangoJobStore(), "default")


@scheduler.scheduled_job("interval", seconds=10, id="test")
def test_job():
    time.sleep(4)
    print "I'm a test job!"
    # raise ValueError("Olala!")

def listener(event):
    print event, type(event), event.__dict__

register_events(scheduler)
# scheduler.add_listener(listener)

scheduler.start()


print "Scheduler started!"