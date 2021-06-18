SECRET_KEY = "secret"

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "helusers.apps.HelusersConfig",
    "helusers.apps.HelusersAdminConfig",
    "helusers.tests",
)

AUTH_USER_MODEL = "tests.User"

OIDC_API_TOKEN_AUTH = {
    "AUDIENCE": "test_audience",
    "ISSUER": ["https://test_issuer_1", "https://test_issuer_2"],
    "REQUIRE_API_SCOPE_FOR_AUTHENTICATION": False,
    "API_AUTHORIZATION_FIELD": "",
    "API_SCOPE_PREFIX": "",
    "OIDC_CONFIG_EXPIRATION_TIME": 2,
}

HELUSERS_BACK_CHANNEL_LOGOUT_ENABLED = True

ROOT_URLCONF = "helusers.urls"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
