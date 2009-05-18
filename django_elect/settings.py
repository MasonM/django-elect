from django.conf import settings


DJANGO_ELECT_MEDIA_ROOT = getattr(settings, 'DJANGO_ELECT_MEDIA_ROOT',
    '/media')
LOGIN_URL = getattr(settings, 'LOGIN_URL', '/account')
