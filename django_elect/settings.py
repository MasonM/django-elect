from django.conf import settings
import os
import django_elect

DJANGO_ELECT_MEDIA_ROOT = getattr(settings, 'DJANGO_ELECT_MEDIA_ROOT',
    '/media')
LOGIN_URL = getattr(settings, 'LOGIN_URL', '/account')
