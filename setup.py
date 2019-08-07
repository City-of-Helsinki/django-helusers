# -*- coding: utf-8 -*-
import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-helusers',
    version='0.4.6',
    packages=['helusers'],
    include_package_data=True,
    license='BSD License',
    description='Django app for the user infrastructure of the City of Helsinki',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/City-of-Helsinki/django-helusers',
    author='City of Helsinki',
    author_email='dev@hel.fi',
    install_requires=[
        'Django',
        'drf-oidc-auth>=0.9',
        'requests',
        'python-jose',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
