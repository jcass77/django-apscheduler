# Django APScheduler

`APScheduler <https://github.com/agronholm/apscheduler>`_ for `Django <https://github.com/django/django>`_.

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
  
  # If you want all scheduled jobs to use this store by default,
  # use the name 'default' instead of 'djangojobstore'.
  scheduler.add_jobstore(DjangoJobStore(), 'djangojobstore')
  
* Register any jobs as you would normally. Note that if you haven't set ``DjangoJobStore`` as the ``'default'`` job store, you'll need to include ``jobstore='djangojobstore'`` in your ``scheduler.add_job`` calls.  
  
* Start the scheduler:
.. code-block:: python

  scheduler.start()
