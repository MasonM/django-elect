from django.conf import settings
from django.db.models.functions import Concat
from django.db.models import Value as V


"""
A string that corresponds to the path to the model that should be used for
the Election.allowed_voters and Vote.account foreign keys. This is mainly for
sites that extend the User model via inheritance, as detailed at
http://scottbarnham.com/blog/2008/08/21/extending-the-django-user-model-with-inheritance/
"""
DJANGO_ELECT_USER_MODEL = getattr(settings,
    'DJANGO_ELECT_USER_MODEL', settings.AUTH_USER_MODEL)


"""
Function to filter a queryset on the user model with a free-form query.
Used by django_elect.autocomplete.AccountAutocomplete.
"""
DJANGO_ELECT_USER_AUTOCOMPLETE_FILTER = getattr(settings,
    'DJANGO_ELECT_USER_AUTOCOMPLETE_FILTER',
    lambda queryset, query: queryset.annotate(
        full_name=Concat('first_name', V(' '), 'last_name')
    ).filter(full_name__icontains=query))


"""
List of tuples to pass to Migration.depedencies for django_elect migrations
"""
DJANGO_ELECT_MIGRATION_DEPENDENCIES = getattr(settings,
    'DJANGO_ELECT_MIGRATION_DEPENDENCIES', [('auth', '0001_initial')])


"""
URL to redirect voters to who are not logged in.
"""
LOGIN_URL = getattr(settings, 'LOGIN_URL', '/account/')
