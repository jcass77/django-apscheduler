import time
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events


scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")

@scheduler.scheduled_job("interval", seconds=10, id="test")
def test_job():
    time.sleep(4)
    print "I'm a test job!"
    # raise ValueError("Olala!")

register_events(scheduler)

scheduler.start()
print "Scheduler started!"