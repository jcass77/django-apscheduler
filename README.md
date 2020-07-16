Django APScheduler
==================

[![Build status](http://travis-ci.org/jarekwg/django-apscheduler.svg?branch=master)](http://travis-ci.org/jarekwg/django-apscheduler)
[![codecov](https://codecov.io/gh/jarekwg/django-apscheduler/branch/master/graph/badge.svg)](https://codecov.io/gh/jarekwg/django-apscheduler)
[![PyPI version](https://badge.fury.io/py/django-apscheduler.svg)](https://badge.fury.io/py/django-apscheduler)
[![Code style:black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://pypi.org/project/black/)

[APScheduler](https://github.com/agronholm/apscheduler) for [Django](https://github.com/django/django).

This is a Django app that adds a lightweight wrapper around APScheduler. It enables storing persistent jobs in the database using Django's ORM.

Features of this package includes:

* Get an overview of the jobs that have been scheduled via the Django admin interface.
* Monitor job execution and status via the Django admin interface

Installation
------------

```python
pip install django-apscheduler
```

Quick start
-----------

* Add ``django_apscheduler`` to your ``INSTALLED_APPS`` setting like this:
```python
  INSTALLED_APPS = (
    ...
    "django_apscheduler",
  )
```

* You can also specify a different format for displaying runtime timestamps in the Django admin site using ``APSCHEDULER_DATETIME_FORMAT``:
```python
  APSCHEDULER_DATETIME_FORMAT =  "N j, Y, f:s a"  # Default
```

* Run `python manage.py migrate` to create the django_apscheduler models.

* Instantiate a new scheduler as you would with APScheduler. For example:
```python
  from apscheduler.schedulers.background import BackgroundScheduler

  scheduler = BackgroundScheduler()
```

* Instruct the scheduler to use `DjangoJobStore`:
```python
  from django_apscheduler.jobstores import DjangoJobStore

  # If you want all scheduled jobs to use this store by default, # use the name 'default' instead of 'djangojobstore'.
  scheduler.add_jobstore(DjangoJobStore(), 'djangojobstore')
```

* If you want per-execution monitoring, call `register_events` on your scheduler:
```python
    from django_apscheduler.jobstores import register_events
    register_events(scheduler)
```

*  Old job executions can be deleted with:
```python
    DjangoJobExecution.objects.delete_old_job_executions(604_800)  # Delete job executions older than 7 days
```

* Register any jobs as you would normally. Note that if you haven't set `DjangoJobStore` as the `'default'` job store,
  then you will need to include `jobstore='djangojobstore'` in your `scheduler.add_job` calls.

* **Don't forget to give each job a unique id using the `id` parameter. For example:**
```python
  @scheduler.scheduled_job("interval", seconds=60, id="job")
  def job():
    pass
```
or use the custom `register_job` decorator for job registration. This will assign a unique id automatically:
```python
  from django_apscheduler.jobstores import register_job

  @register_job("interval", seconds=60)
  def job():
    pass
```

* Start the scheduler:
```python
  scheduler.start()
```

A full example project can be found in the 'examples' folder. Code snippet:
```python
import time

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job

scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")

@register_job(scheduler, "interval", seconds=1)
def test_job():
    time.sleep(4)
    print("I'm a test job!")
    # raise ValueError("Olala!")

register_events(scheduler)

scheduler.start()
print("Scheduler started!")
```
