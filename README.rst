=====
Django app for City of Helsinki user infrastructure
=====

Installation
------------

First, install the pip package.

.. code:: shell

  pip install django-helusers

Second, modify your ``settings.py`` to add the ``helusers`` app and
to use the modified User model.

.. code:: python

  INSTALLED_APPS = (
      ...
      'helusers',
      ...
  )

  AUTH_USER_MODEL = 'helusers.User'
