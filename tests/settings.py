
SECRET_KEY = 'NOTASECRET'

INSTALLED_APPS = [
    'django_apscheduler'
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'TEST_NAME': ':memory:',
        'NAME': 'db'
    },
}
