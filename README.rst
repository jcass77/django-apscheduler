Django APScheduler
==================
APScheduler for Django.

This little wrapper around APScheduler enables storing persistent jobs in the database using Django's ORM rather than requiring SQLAlchemy or some other bloatware.

Usage
-----

* Add ``django_apscheduler`` to ``INSTALLED_APPS`` in your Django project settings:
.. code-block:: python

  INSTALLED_APPS = (
    ...
    django_apscheduler,
  )
  
* Run migrations:
.. code-block:: python

  ./manage.py migrate
  
* Instanciate a new scheduler as you would with APScheduler. For example:
.. code-block:: python

  from apscheduler.schedulers.background import BackgroundScheduler
  
  scheduler = BackgroundScheduler()
  
* Instruct the scheduler to use ``DjangoJobStore``:
.. code-block:: python

  from django_apscheduler.jobstores import DjangoJobStore
  
  scheduler.add_jobstore(DjangoJobStore(), 'djangojobstore')

* Start the scheduler as normal:
.. code-block:: python

  scheduler.start()
