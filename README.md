[![Build status](https://travis-ci.org/City-of-Helsinki/django-helusers.svg?branch=master)](https://travis-ci.org/City-of-Helsinki/django-helusers)
[![codecov](https://codecov.io/gh/City-of-Helsinki/django-helusers/branch/master/graph/badge.svg)](https://codecov.org/gh/City-of-Helsinki/django-helusers)
[![Requirements](https://requires.io/github/City-of-Helsinki/django-helusers/requirements.svg?branch=master)](https://requires.io/github/City-of-Helsinki/django-helusers/requirements/?branch=master)

# Django app for City of Helsinki user infrastructure

## Installation

First, install the pip package.

```bash
pip install django-helusers
```

Second, implement your own custom User model in your application's
`models.py`.

```python

# users/models.py

from helusers.models import AbstractUser


class User(AbstractUser):
    pass
```

### Configuration of the auth provider

- Add `social-auth-app-django` to your `requirements.in` or `requirements.txt` file and install the package.
- Add `helusers` and `social_django` to the `INSTALLED_APPS` setting:

```python
INSTALLED_APPS = (
    'helusers',
    ...
    'social_django',
    ...
)
```

***Note*** `helusers` must be the first one in the list to properly override the default admin site templates.

- Configure the following settings:

```python
SOCIAL_AUTH_POSTGRES_JSONFIELD = True

AUTHENTICATION_BACKENDS = (
    'helusers.helsinki_oidc.HelsinkiOIDCAuth',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_USER_MODEL = 'users.User'
LOGIN_REDIRECT_URL = '/'
```

- Add URLs entries (to `<project>/urls.py`):

```python
urlpatterns = patterns('',
    ...
    path('', include('social_django.urls', namespace='social'))
    ...
)
```

- Configure your client ID, secret and OIDC endpoint locally (for example in `local_settins.py`):

```python
TUNNISTAMO_BASE_URL = 'https://tunnistamo.example.com'
SOCIAL_AUTH_TUNNISTAMO_KEY = 'abcd-12345-abcd-12356789'
SOCIAL_AUTH_TUNNISTAMO_SECRET = 'abcd1234abcd1234abcd1234abcd1234'
SOCIAL_AUTH_TUNNISTAMO_OIDC_ENDPOINT = TUNNISTAMO_BASE_URL + '/openid'
```

### Configuration of the API authentication (using JWT tokens)

- Configure REST framework to use the `ApiTokenAuthentication` class in `settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'helusers.oidc.ApiTokenAuthentication',
    ),
}
```

- Set your deployment-specific variables in `local_settings.py`, e.g.:

```python
OIDC_API_TOKEN_AUTH = {
    'AUDIENCE': 'https://api.hel.fi/auth/projects',
    'API_SCOPE_PREFIX': 'projects',
    'REQUIRE_API_SCOPE_FOR_AUTHENTICATION': True,
    'ISSUER': 'https://api.hel.fi/sso/openid'
}
```

### Context processor

If you need to access the Tunnistamo API from your JS code, you can include
the Tunnistamo base URL in your template context using helusers's context processor:

```python
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                'helusers.context_processors.settings'
            ]
        }
    }
]
```
