# Overview

django-elect is a simple voting app intended for small-scale elections within academic
organizations. It relies on Django's authentication system for verifying voter identity.

# Features

* Highly customizable and easy-to-use admin interface.
* Supports both preferential (using the Borda count method) and plurality ballots with optional secrecy.
* Supports write-in candidates.
* Customizable biographies page with biographical information on each candidate.
* Statistics page with up-to-date election results.
* Can generate Excel spreadsheets with complete election data.

# Dependencies

* Python 2.7
* Django 1.8+
* [django-autocomplete-light 3.0+](https://github.com/yourlabs/django-autocomplete-light)

# Installation
Run `python setup.py install` to install django-elect and any missing dependencies.

# Using in an Existing Django Project
If you want to integrate django-elect with an existing project, follow these steps:

1. Add `"django_elect"` to the `INSTALLED_APPS` tuple in the project's `settings.py` file.
2. Add `django-autocomplete-light` to `INSTALLED_APPS` [as detailed here](https://django-autocomplete-light.readthedocs.io/en/master/install.html#install-in-your-project).
3. Add `(r'^election/', include('django_elect.urls')),` to the project's `urls.py` file.

# Using Standalone
If you don't have an existing Django project, you'll need to create one. Use the
project in the "example_project" directory as a starting point and customize the settings.py file
for your server. See the following pages for more information:

* [Deploying Django](http://docs.djangoproject.com/en/dev/howto/deployment/)
* [Django settings documentation](http://docs.djangoproject.com/en/dev/topics/settings/)
