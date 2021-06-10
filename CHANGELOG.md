# Changelog

## 0.6.1 - 2021-06-10

### Added

- Set django-heluers' default auto field to be `django.db.models.AutoField` for [Django versions >=3.2](https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys) to avoid unwanted migrations.

## 0.6.0 - 2021-01-18

### Added

- An authentication/JWT validation service with minimal external dependencies: `helusers.oidc.RequestJWTAuthentication`.

### Changed

- Supported Python versions: 3.6-3.9.
- Previously `drf-oidc-auth` was a hard dependency in `django-helusers`. That's no longer the case. Within `django-helusers` the `drf-oidc-auth` package is only used by the `helusers.oidc.ApiTokenAuthentication` class. If you want to keep on using that class, make sure you bring `drf-oidc-auth` into your project as an explicit dependency.
- `django-helusers` has been very much dependent on Django REST Framework (DRF), even though the user of `django-helusers` wouldn't otherwise need DRF. This dependency has been removed: it's now possible to use `django-helusers` without DRF.

### Fixed

- Whenever `django-helusers` returns or provides a `User` object, the `uuid` field is always of type `UUID` (previously it was sometimes of type `str`).
