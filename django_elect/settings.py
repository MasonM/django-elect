from django.conf import settings


"""
A tuple of the form (app_name, model) that corresponds to the model that should
that should be used for the Election.allowed_voters and Vote.account foreign
keys. This is mainly for sites that extend the User model via inheritance, as
detailed at
http://scottbarnham.com/blog/2008/08/21/extending-the-django-user-model-with-inheritance/
"""
DJANGO_ELECT_USER_MODEL = getattr(settings,
    'DJANGO_ELECT_USER_MODEL', ('auth', 'User'))


"""
URL to redirect voters to who are not logged in.
"""
LOGIN_URL = getattr(settings, 'LOGIN_URL', '/account/')
