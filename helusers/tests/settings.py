from helusers.defaults import SOCIAL_AUTH_PIPELINE  # noqa: F401

USE_TZ = True

SECRET_KEY = "secret"

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "helusers.apps.HelusersConfig",
    "helusers.apps.admin.HelusersAdminConfig",
    "social_django",
    "helusers.tests",
)

AUTH_USER_MODEL = "tests.User"

SESSION_SERIALIZER = "helusers.sessions.TunnistamoOIDCSerializer"

AUTHENTICATION_BACKENDS = [
    "helusers.tunnistamo_oidc.TunnistamoOIDCAuth",
    "django.contrib.auth.backends.ModelBackend",
]
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

OIDC_API_TOKEN_AUTH = {
    "AUDIENCE": "test_audience",
    "ISSUER": ["https://test_issuer_1", "https://test_issuer_2"],
    "REQUIRE_API_SCOPE_FOR_AUTHENTICATION": False,
    "API_AUTHORIZATION_FIELD": "",
    "API_SCOPE_PREFIX": "",
    "OIDC_CONFIG_EXPIRATION_TIME": 2,
}

SOCIAL_AUTH_TUNNISTAMO_KEY = "test-client-id"
SOCIAL_AUTH_TUNNISTAMO_SECRET = "iamyoursecret"
SOCIAL_AUTH_TUNNISTAMO_OIDC_ENDPOINT = "https://test_issuer_1"

HELUSERS_BACK_CHANNEL_LOGOUT_ENABLED = True

ROOT_URLCONF = "helusers.tests.urls"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
