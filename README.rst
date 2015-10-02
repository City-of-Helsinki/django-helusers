=====
Django app for City of Helsinki user infrastructure
=====

Installation
------------

First, install the pip package.

.. code:: shell

  pip install django-helusers

Second, implement your own custom User model in your application's
``models.py``.

.. code:: python

  from helusers.models import AbstractUser


  class User(AbstractUser):
      pass

Then, modify your ``settings.py`` to add the ``helusers`` app and
point Django to use your custom User model.

.. code:: python

  INSTALLED_APPS = (
      ...
      'helusers',
      ...
  )

  AUTH_USER_MODEL = 'myapp.User'


OAuth2 provider
---------------

If you want to use the City's OAuth2 API, you need to install the
``django-allauth`` package. Follow the `installation instructions
<http://django-allauth.readthedocs.org/en/latest/installation.html>`_
provided by ``django-allauth``.

Then, install the allauth provider by adding ``helusers.providers.helsinki``
to your ``INSTALLED_APPS``.
