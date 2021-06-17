# Changelog

This changelog is used to track all major changes to django-apscheduler.

## v0.6.0 (2021-06-17)

**Fixes**

- Fix screenshot links in README to work on PyPI.
- Remove reference to deprecated `django.utils.translation.ugettext_lazy`.

**Enhancements**

- The Django admin page will now show a list of all the manually triggered jobs that could not be completed
  before `settings.APSCHEDULER_RUN_NOW_TIMEOUT` seconds elapsed.
- Make more of the string output on the admin page Django-translatable.
- Introduce a `retry_on_db_operational_error` utility decorator for retrying database-related operations when
  a `django.db.OperationalError` is encountered (Partial resolution
  of [#145](https://github.com/jcass77/django-apscheduler/issues/145)).
- Introduce a `close_old_connections` utility decorator to enforce Django's `CONN_MAX_AGE` setting. (Partial resolution
  of [#145](https://github.com/jcass77/django-apscheduler/issues/145)). **This decorator should be applied to all of
  your jobs that require access to the database.**

## v0.5.2 (2021-01-28)

**Enhancements**

- Include Python 3.9 in continuous integration runs.
- Switch from Travis-CI to GitHub Actions.

## v0.5.1 (2020-11-06)

**Fixes**

- Pin dependency to APScheduler < 4.0, which appears to be introducing
  some [backwards incompatible changes](https://github.com/agronholm/apscheduler/issues/465).
- Update readme to clarify the need for ensuring that a single scheduler is run in your Django application until
  APScheduler 4.0 arrives and django-apscheduler is migrated to make use of that version.
- Update authors section in `setup.py`.
- Don't try to log job executions for jobs that are no longer available in the job store. This was partially fixed
  previously as part of [#116](https://github.com/jcass77/django-apscheduler/issues/116), which only catered for
  'execution' type of events. This fix resolves the issue for the remaining 'submitted' and 'error' events as well
  (Fixes [#121](https://github.com/jcass77/django-apscheduler/issues/121)).


## v0.5.0 (2020-10-13)

**Enhancements**

- Add ability to trigger a scheduled job manually from the `DjangoJobAdmin` page (
  Resolves [#102](https://github.com/jcass77/django-apscheduler/issues/102)).
- The `@register_job` decorator has been deprecated. Please use APScheduler's `add_job()` method or `@scheduled_job`
  decorator instead (Resolves [#119](https://github.com/jcass77/django-apscheduler/pull/119)).

**Fixes**

- Don't try to log job executions for jobs that are no longer available in the job store (
  Fixes [#116](https://github.com/jcass77/django-apscheduler/issues/116)).


## v0.4.2 (2020-08-11)

**Fixes**

- Fix mapping of event listener APScheduler codes to event classes (
  Fixes [#98](https://github.com/jcass77/django-apscheduler/issues/98)).


## v0.4.1 (2020-08-09)

**Fixes**

- Drop use of `of` parameter in `select_for_update`, which is not supported by MariaDB and MySQL (
  Fixes [#94](https://github.com/jcass77/django-apscheduler/issues/94)).


## v0.4.0 (2020-07-27)

**Enhancements**

- Drop support for Python 2.7, convert codebase to Python 3.6+.
- CI: drop coverage for Python 2.7 and Django <= 2.1, which are no longer maintained upstream.
- CI: add coverage for Python 3.7 and 3.8, as well as Django long term support (LTS) and the latest released versions.
- CI: un-pin dependency on agronholm/apscheduler#149, which has since been merged and released upstream.
- Rename Django `test_settings.py` file to prevent collision with actual test scripts.
- Clean up unused dependencies / update dependencies to latest available versions.
- Switch to Black code formatting.
- Align package layout with official [Django recommendations](https://docs.djangoproject.com/en/dev/intro/reusable-apps/#packaging-your-app)
- Move UI-related `DjangoJobExecution.html_status` out of model definition and in to the associated model admin definition.
- Add `help_text` to model fields to document their use.
- Remove unused code fragments.
- Add Python type annotations.
- Implement various Django best practices for QuerySet management and model instance creation / updates.
- Drop `DjangoJob.name` field in favor of aligning with using APScheduler's `id` field. NOTE: please run your Django
  migrations again - might take a while depending on the number of `DjangoJobExecutions` in your database.
- Acquire a DB lock when updating `DjangoJob` or `DjangoJobExecution` instances. This should be safer for multi-threaded
  usage.
- Switch to using `BigAutoField` for `DjangoJobExecution`'s primary keys. This should prevent running out of usable ID's
  for deployments with a very large number of job executions in the database (
  Resolves [#36](https://github.com/jcass77/django-apscheduler/issues/36)).
- Implement `DjangoJob.shutdown()` method to close database connection when scheduler is shut down.
- `jobstores.register_events` has been deprecated and will be removed in a future release. Calling this method is no
  longer necessary as the `DjangoJobStore` will automatically register for events that it cares about when the scheduler
  is started.
- Ensure that Django and APScheduler always use the same timezones when passing datetimes between the two.
- Use the configured scheduler's locking mechanism to keep the creation of `DjangoJobExecution` in sync with APScheduler
  events.
- Update README on recommended usage, which includes using a `BlockingScheduler` with a custom Django management command
  instead of running a `BackgroundScheduler` directly in a Django application.
- Remove `ignore_database_error` decorator. All database errors will be raised so that users can decide on the best
  course of action for their specific use case (Resolves [#79](https://github.com/jcass77/django-apscheduler/issues/79))
  .
- Remove `DjangoJobManager`: users should be allowed to manage the DB connection themselves based on their
  implementation-specific use case. See the official Django recommendations at: https://code.djangoproject.com/ticket/21597#comment:29.
- Add AUTHORS file.
- Increase test coverage.
- Remove the `DjangoJobExecution.started` field. It appears that APScheduler only fires an event when the job is
  submitted to the scheduler (not when job execution actually starts). We now calculate the job `duration` as the
  elapsed time in seconds between the scheduled `run_time` and when we receive the `events.EVENT_EXECUTED`
  APScheduler event. 

**Fixes**

- Fix PEP8 code formatting violations.
- Implement locking mechanism to prevent duplicate `DjangoJobExecution`s from being created (
  Fixes [#28](https://github.com/jcass77/django-apscheduler/issues/28)
  , [#30](https://github.com/jcass77/django-apscheduler/issues/30)
  , [#44](https://github.com/jcass77/django-apscheduler/issues/44)).
- `DjangoJobStore.add_job` now raises a `ConflictingIdError` if a job with that particular ID already exists in the job
  store. This aligns with the behavior expected by the APScheduler interface. Use the `replace_existing` parameter to
  update existing jobs instead.

## v0.3.1 (2020-07-12)

- Various bug fixes (see commit history for changes).


## v0.3.0 (2019-04-03)

- Added timezone support when rendering datetimes; dropped support for django1.8 (
  Fixes [#43](https://github.com/jcass77/django-apscheduler/issues/43) - thanks @jcass77).
- Added model manager for deleting old job executions (
  Fixes [#58](https://github.com/jcass77/django-apscheduler/issues/58) - thanks @jcass77).


## v0.2.13 (2018-09-01)

- Fixed exception when removing failed jobs (Fixes [#33](https://github.com/jcass77/django-apscheduler/issues/33)).
- Accounted for `dt` coming in as `None` into `serialize_dt` (
  Fixes [#35](https://github.com/jcass77/django-apscheduler/issues/35)).


## v0.2.12 (2018-07-10)

- Fix of [#26](https://github.com/jcass77/django-apscheduler/issues/26).


## v0.2.10 (2018-06-05)

- This release covers this PR [#23](https://github.com/jcass77/django-apscheduler/issues/23), thanks to @nialllo


## v0.2.9 (2018-05-08)

- Now `add_job` with duplicated job `id` will refresh job in database instead of raising an exception.


## v0.2.8 (2018-04-28)

- Fixed bug [#20](https://github.com/jcass77/django-apscheduler/issues/20).
- Changed logger from `default` to `django_apscheduler`.
- Added `on_error_value` into `ignore_database_error` (to return empty array instead of `None` in some methods).
- Added django==1.8 test env in tox.ini


## v0.2.7 (2018-04-14)

- Fixed issue (Fixes [#18](https://github.com/jcass77/django-apscheduler/issues/18)).
- Added check whether `connections.connection` is `None`.


## v0.2.6 (2018-04-12)

- This release closes bugs described in (Fixes [#15](https://github.com/jcass77/django-apscheduler/issues/15)).
- After updating, please run `./manage.py migrate django_apscheduler` to apply the latest database changes.


## v0.2.5 (2018-02-01)

- Fix [#13](https://github.com/jcass77/django-apscheduler/issues/13).
- Added exception handling when system tables doesn't exists


## v0.2.3 (2017-12-10)

- Underscore changed to hyphen in pypi package name.  


## v0.2.2 (2017-12-10)

- Django 2.x support.


## Pre-releases

- The project did not tag a number of pre-release versions.
