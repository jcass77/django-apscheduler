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
