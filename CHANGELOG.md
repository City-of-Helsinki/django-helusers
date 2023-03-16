# Changelog

## 0.8.0 - 2023-03-16

### Added

- Support for Python 3.10 & 3.11
- Support for Django >=4.0

### Removed

- Support for Python 3.6
- Support for Django 2.2

## 0.7.1 - 2022-04-12

### Changed

- Handle a list of configured issuers in `ApiTokenAuthentication`
- Require Django version < 4

## 0.7.0 - 2021-08-16

### Added

- An [OIDC back channel logout](https://openid.net/specs/openid-connect-backchannel-1_0.html) endpoint implementation.

### Changed

- Set required Django version to 2.2 and later.

### Removed

- The `key_provider` argument of `helusers.oidc.RequestJWTAuthentication.__init__` method was removed. It existed only for test support, but tests have been modified in a way that it's not needed any more.

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
