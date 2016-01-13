#!/usr/bin/env python
import sys
import os
from os.path import dirname, abspath
from optparse import OptionParser

from django.conf import settings

if not settings.configured and not os.environ.get('DJANGO_SETTINGS_MODULE'):
    settings.configure(
        DATABASES = {
            'default': {
                "ENGINE": 'django.db.backends.mysql',
                "NAME": 'election',
                "USER": 'electionUser',
                "PASSWORD": 'electionPass',
            }
        },
        INSTALLED_APPS = [
            'django.contrib.auth',
            'django.contrib.admin',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.staticfiles',

            'django_elect',
        ],
        SERIALIZATION_MODULES = {},
        STATIC_URL = '/static/',
        LOGIN_URL = '/account/',
        ROOT_URLCONF = 'django_elect.urls',
        DEBUG = True,
        SITE_ID = 1,
    )

from django.test.utils import setup_test_environment
from django.test.runner import DiscoverRunner

def runtests(options):
    parent = dirname(abspath(__file__))
    sys.path.insert(0, parent)
    setup_test_environment()
    test_runner = DiscoverRunner(**options)
    failures = test_runner.run_tests(['django_elect'])
    sys.exit(failures)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--verbosity', default=1, dest='verbosity')
    parser.add_option('--interactive', action='store_true', default=False,
        dest='interactive')
    parser.add_option('--failfast', action='store_true', default=False,
        dest='failfast')

    (options, args) = parser.parse_args()

    runtests(vars(options))
