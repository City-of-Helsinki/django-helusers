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
AUTHENTICATION_BACKENDS = (
    'helusers.tunnistamo_oidc.TunnistamoOIDCAuth',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_USER_MODEL = 'users.User'
LOGIN_REDIRECT_URL = '/'
```
- If you need to be able to control Tunnistamo login process language, add also setting
```python
SOCIAL_AUTH_TUNNISTAMO_AUTH_EXTRA_ARGUMENTS = {'ui_locales': 'fi'}
```
`fi` there is the language code that will be used when no language is requested, so change it if you you prefer some
other default language. If you don't want to set a default language at all, use an empty string `""` as the language
code.

When that setting is in place, languages can be requested using query param `ui_locales=<language code>` when starting
the login process, for example in your template
```
<a href="{% url 'helusers:auth_login' %}?next=/foobar/&ui_locales=en">Login in English</a>
```

- Add URLs entries (to `<project>/urls.py`):

```python
urlpatterns = patterns('',
    ...
    path('', include('social_django.urls', namespace='social'))
    ...
)
```

- Configure your client ID, secret and OIDC endpoint locally (for example in `local_settings.py`):

```python
TUNNISTAMO_BASE_URL = 'https://tunnistamo.example.com'
SOCIAL_AUTH_TUNNISTAMO_KEY = 'abcd-12345-abcd-12356789'
SOCIAL_AUTH_TUNNISTAMO_SECRET = 'abcd1234abcd1234abcd1234abcd1234'
SOCIAL_AUTH_TUNNISTAMO_OIDC_ENDPOINT = TUNNISTAMO_BASE_URL + '/openid'
```

- Set the session serializer to PickleSerializer

helusers stores the access token expiration time as a datetime which is not
serializable to JSON, so Django needs to be configured to use the built-in
PickeSerializer:

```python
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
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

### Disabling password logins

If you're not allowing users to log in with passwords, you may disable the
username/password form from Django admin login page by setting `HELUSERS_PASSWORD_LOGIN_DISABLED`
to `True`.
