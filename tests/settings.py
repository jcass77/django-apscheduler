SECRET_KEY = "NOTASECRET"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.admin",
    "django_apscheduler",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "TEST_NAME": ":memory:",
        "NAME": "db",
    },
}

APSCHEDULER_RUN_NOW_TIMEOUT = 15
APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"
