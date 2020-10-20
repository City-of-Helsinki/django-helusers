SECRET_KEY = "secret"

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "helusers.apps.HelusersConfig",
    "helusers.apps.HelusersAdminConfig",
    "helusers.tests",
)

AUTH_USER_MODEL = "tests.User"

OIDC_API_TOKEN_AUTH = {
    "AUDIENCE": "test_audience",
}
