[![Build status](https://travis-ci.org/City-of-Helsinki/django-helusers.svg?branch=master)](https://travis-ci.org/City-of-Helsinki/django-helusers)
[![codecov](https://codecov.io/gh/City-of-Helsinki/django-helusers/branch/master/graph/badge.svg)](https://codecov.org/gh/City-of-Helsinki/django-helusers)
[![Requirements](https://requires.io/github/City-of-Helsinki/django-helusers/requirements.svg?branch=master)](https://requires.io/github/City-of-Helsinki/django-helusers/requirements/?branch=master)

# Django app for City of Helsinki user infrastructure

django-helusers is your friendly app for bolting authentication into Django projects for City of Helsinki. It provides the following functionalities:

* baseline User model
* authentication against Tunnistamo, an OIDC service for authenticating against multiple backends
* augmented login template for for Django admin, allowing tunnistamo login
* mapping from Tunnistamo provided AD groups to Django groups
* integration with Django Rest Framework authentication
* authenticating DRF requests using a Tunnnistamo specific "API Token"

## Adding django-helusers your Django project

Add:

* `django-helusers`
* `social-auth-app-django`

to your dependency management list. Django-helusers depends on
`social-auth-app-django` for implementation of the OIDC dance.

### Adding user model

helusers provides a baseline user model adding fields for Helsinki
specific information. As per Django [best practice](https://docs.djangoproject.com/en/3.0/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project)
you should subclass this model to make future customization easier:

```python

# users/models.py

from helusers.models import AbstractUser


class User(AbstractUser):
    pass
```

and reference it in settings.py:

```python
# myproject/settings.py

AUTH_USER_MODEL = 'users.User'
```

### Adding django-helusers Django apps

Django-helusers provides two Django apps: `HelusersConfig` provides the
models and templates needed for helusers to work and `HelusersAdminConfig`
reconfigures Django admin to work with helusers. The latter includes adding
a Tunnistamo login button to the admin login screen.

Additionally `social_django` app is needed for the underlying python-social-auth.

Add these apps to your `INSTALLED_APPS` in settings.py:

```python
INSTALLED_APPS = (
    'helusers.apps.HelusersConfig',
    'helusers.apps.HelusersAdminConfig',
    ...
    'social_django',
    ...
)
```

Us usual with `INSTALLED_APPS`, ordering matters. `HelusersConfig` must come
before `HelusersAdminConfig` and anything else providing admin templates.
Unless, of course, you wish to override the admin templates provided here.

One possible gotcha is, if you've added custom views to admin without
forwarding context from `each_context` to the your template.  Helusers
templates expect variables from `each_context` and will break if they are
missing.

### Adding Tunnistamo authentication

django-helusers ships with backend for authenticating against Tunnistamo
using OIDC. There is also a deprecated legacy OAuth2 backend using
allauth framework.

Typically you would want to support authenticating using both OIDC and local
database tables. Local users are useful for initial django admin login, before
you've delegated permissions to users coming through OIDC.

Add backend configuration to your `settings.py`:

```python
AUTHENTICATION_BACKENDS = (
    'helusers.tunnistamo_oidc.TunnistamoOIDCAuth',
    'django.contrib.auth.backends.ModelBackend',
)
LOGIN_REDIRECT_URL = '/'
```

`LOGIN_REDIRECT_URL` is the default landing URL after succesful login, if your
form did not specify anything else.

You will also need to add `python-social-auth` URLs to your URL dispatcher
configuration (`urls.py`):

```python
urlpatterns = patterns('',
    ...
    path('', include('social_django.urls', namespace='social'))
    ...
)
```

Finally, you will need to configure your SESSION_SERIALIZER. helusers stores
the access token expiration time as a datetime which is not serializable
to JSON, so Django needs to be configured to use the built-in
PickleSerializer:

```python
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
```

### Configuration of the DRF API authentication (using JWT tokens)

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

### Adding tunnistamo URL to template context

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

### Carrying language preference from your application to Tunnistamo

Tunnistamo (per the OIDC specs) allows clients to specify the language used for
the login process. This allows you to carry your applications language setting
to the login screens presented by Tunnistamo.

Configure `python-social-auth` to pass the necessary argument through its
login view:
```python
SOCIAL_AUTH_TUNNISTAMO_AUTH_EXTRA_ARGUMENTS = {'ui_locales': 'fi'}
```
`fi` there is the language code that will be used when no language is requested, so change it if you you prefer some
other default language. If you don't want to set a default language at all, use an empty string `""` as the language
code.

When this setting is in place, languages can be requested using query param `ui_locales=<language code>` when starting
the login process, for example in your template
```
<a href="{% url 'helusers:auth_login' %}?next=/foobar/&ui_locales=en">Login in English</a>
```

## Configuring your installation

Each installation ("client" in OIDC parlance) will need its own configuration in Tunnistamo and
matching configuration in your project config file. Usually three pieces of information are needed:
* client ID
* client secret
* Tunnistamo OIDC endpoint

Additionally you will need to provide your "callback URL" to the folks configuring Tunnistamo.
This is implemented by `python-social-auth` and will, by default, be
`https://app.domain/auth/complete/tunnistamo/`. During development on your own laptor your
`app.domain` would be `localhost`.

After you've received your client ID, client secret and Tunnistamo OIDC endpoint you would
configure them as follows:
```python
SOCIAL_AUTH_TUNNISTAMO_KEY = 'abcd-12345-abcd-12356789'
SOCIAL_AUTH_TUNNISTAMO_SECRET = 'abcd1234abcd1234abcd1234abcd1234'
SOCIAL_AUTH_TUNNISTAMO_OIDC_ENDPOINT = https://tunnistamo.example.com/
```

Note that `client ID` becomes `KEY` and `client secret` becomes `SECRET`.

### Disabling password logins

If you're not allowing users to log in with passwords, you may disable the
username/password form from Django admin login page by setting `HELUSERS_PASSWORD_LOGIN_DISABLED`
to `True`.
