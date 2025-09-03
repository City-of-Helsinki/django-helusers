# Changelog

## [0.14.0](https://github.com/City-of-Helsinki/django-helusers/compare/django-helusers-v0.13.3...django-helusers-v0.14.0) (2025-09-01)


### Features

* Add api_token_used field to AbstractUser ([f66dce5](https://github.com/City-of-Helsinki/django-helusers/commit/f66dce518dd33876732c15034909fb9929709ad7))
⚠️ Remember to **create migration** for the inherited user model! ⚠️

## [0.13.3](https://github.com/City-of-Helsinki/django-helusers/compare/django-helusers-v0.13.2...django-helusers-v0.13.3) (2025-03-10)


### Bug Fixes

* Use "get_success_url"-method ([0305c06](https://github.com/City-of-Helsinki/django-helusers/commit/0305c0663b18de0bb8d5076ad993b995109e0f60))


### Documentation

* **changelog:** Remove unreleased and removed sections ([7fb9c71](https://github.com/City-of-Helsinki/django-helusers/commit/7fb9c710bc67b82418b4f409c3192b3ce37fb83f))

## [0.13.2](https://github.com/City-of-Helsinki/django-helusers/compare/django-helusers-v0.13.1...django-helusers-v0.13.2) (2025-03-03)


### Continuous Integration

* Release-please automatically pushes the package to PyPi ([623d889](https://github.com/City-of-Helsinki/django-helusers/commit/623d889fd0aa7a44dd82143e084f55bae7e1396e))

## [0.13.1](https://github.com/City-of-Helsinki/django-helusers/compare/django-helusers-v0.13.0...django-helusers-v0.13.1) (2025-03-03)


### Bug Fixes

* Map multiple user groups to one ad group ([1600579](https://github.com/City-of-Helsinki/django-helusers/commit/1600579d88f3559201e6d7dd2f642f558f70f79e))


### Documentation

* **readme:** Fix title level for user migration ([7381cda](https://github.com/City-of-Helsinki/django-helusers/commit/7381cda7f2acb1e7804e461994193c3cfbb5b735))
* Update changelog ([f0ccc44](https://github.com/City-of-Helsinki/django-helusers/commit/f0ccc44d21211f51459555d9d4af63e7e7c66dcc))

## 0.13.0 - 2024-06-25

### Added

- Add feature to migrate old users from Tunnistamo to Keycloak upon login. With default settings, only users using AD authentication will be migrated. Feature can be enabled with the setting `HELUSERS_USER_MIGRATE_ENABLED` which defaults to `False`.

### Changed

- Improve ModelAdmins for ADGroupMapping and ADGroup

## 0.12.0 - 2024-05-20

### Changed

- Add new setting `ALLOWED_ALGORITHMS` with a default value of `["RS256"]`

## 0.11.0 - 2024-03-15

### Changed

- Add Django admin logout support for Django 5.0
- Add code quality tooling: black, isort, flake8, commitlint, pre-commit
- Run code quality tools and do the necessary fixes

## 0.10.0 - 2024-03-07

### Changed

- Drop support for Python 3.7 and older
- Add support for Python 3.12
- Require at least Django 3.2
- Add support for Django 5.0 by adding a new session serializer `TunnistamoOIDCSerializer` which can handle session data produced by the custom `helusers.defaults.SOCIAL_AUTH_PIPELINE` pipeline. Django 5.0 removed `PickleSerializer`.

## 0.9.0 - 2023-08-09

### Fixed

- `ApiTokenAuthentication` again validates the `aud` claim. The `aud` claim wasn't validated if the `drf-oidc-auth` version was 1.0.0 or greater.

### Added

- Ability to use "dot notation" in `API_AUTHORIZATION_FIELD` setting for searching api scopes from deeper in the claims
- Documentation about social auth pipeline configuration

### Removed

- Removed `drf-oidc-auth` requirement when using `ApiTokenAuthentication`. Django REST framework is still required.

### Changed

- `API_AUTHORIZATION_FIELD` and `API_SCOPE_PREFIX` settings now support a list of strings
- `ApiTokenAuthentication` is no longer a subclass of `oidc_auth.authentication.JSONWebTokenAuthentication` but a direct subclass of `rest_framework.authentication.BaseAuthentication`
- `ApiTokenAuthentication` uses the same `JWT` class as `RequestJWTAuthentication` for the token validation
  - **Changed** methods:
    - `decode_jwt` can raise `jose.JWTError` exception
    - `get_oidc_config` no longer returns oidc configuration dictionary but an `OIDCConfig` instance
    - `validate_claims` still exists and is called, but doesn't do anything
  - **Removed** methods:
    - `get_audiences`
    - `jwks`
    - `jwks_data`
    - `oidc_config`
  - **Removed** properties:
    - `claims_options`
    - `issuer`

- `ApiTokenAuthentication` now supports multiple issuers. Previously it accepted multiple issuers in the settings but could only use the first issuer.
- `ApiTokenAuthentication.authenticate` no longer raises AuthenticationError if authorization header contains the correct scheme but not a valid JWT-token. Now it just returns None which means the authentication didn't succeed but can be tried with the next authenticator.
- `ApiTokenAuthentication` now rejects tokens if they are invalidated with back-channel log out
- `amr` claim is no longer validated in `ApiTokenAuthentication`
- Issued at (`iat`) claim is no longer limited by the OIDC_LEEWAY oidc_auth setting (default 10 minutes) when using `ApiTokenAuthentication`. i.e. tokens can be generated as long ago as needed.
- User is no longer created if token is correct but is missing the required API scopes in `ApiTokenAuthentication`

## 0.8.1 - 2023-04-04

### Fixed

- Admin site logout view caching with Django 4
- Turn invalid string `amr` claim into an array in JWT

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
