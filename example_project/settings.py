# Django settings for election project.
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    "default": {
        "ENGINE": 'django.db.backends.mysql',
        "NAME": 'election',
        "USER": 'electionUser',
        "PASSWORD": 'electionPass',
        "HOST": '',
        "PORT": '',
        "TEST_NAME": 'election_test',
    },
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

WEB_ROOT = os.getcwd()

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

STATIC_ROOT = WEB_ROOT + "/static/"

STATIC_URL = '/static/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'sh)ip(^)gy+0!n83ayuk599b1()40-^%m*!$4e*ube61w#8fpi'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'example_project.urls'

LOGIN_URL = "/account/"

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    WEB_ROOT + '/templates/',
)

INSTALLED_APPS = (
    'django_elect',
    'dal',
    'dal_select2',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
)
