0.6.0

- Previously `drf-oidc-auth` was a hard dependency in `django-helusers`. That's no longer the case. Within `django-helusers` the `drf-oidc-auth` package is only used by the `helusers.oidc.ApiTokenAuthentication` class. If you want to keep on using that class, make sure you bring `drf-oidc-auth` into your project as an explicit dependency.
