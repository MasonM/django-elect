#!/usr/bin/env python
from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

setup(name='django-elect',
    version='0.1',
    description='A simple voting app for Django',
    license='BSD',
    author='Mason Malone',
    author_email='mason.malone@gmail.com',
    url='http://bitbucket.org/MasonM/django-elect/',
    packages=find_packages(exclude=['example_project', 'example_project.*']),
    include_package_data=True,
    tests_require=[
        'django>=1.8,<1.9',
        'freezegun',
        'unittest2',
    ],
    test_suite='runtests.runtests',
    install_requires=[
        'django>=1.8,<1.9',
        'setuptools',
    ],
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Framework :: Django',
        'Programming Language :: Python',
        'Programming Language :: JavaScript',
        'Topic :: Internet :: WWW/HTTP :: Site Management'],
)

