from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent

env = environ.Env(
    DEBUG=(bool, False),
    DJANGO_DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    DJANGO_ALLOWED_HOSTS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
    DJANGO_CSRF_TRUSTED_ORIGINS=(list, []),
    SESSION_COOKIE_AGE=(int, 3600),
    AXES_FAILURE_LIMIT=(int, 5),
    AXES_COOLOFF_TIME=(float, 1),
    SECURE_SSL_REDIRECT=(bool, False),
    SECURE_HSTS_SECONDS=(int, 0),
    SECURE_HSTS_INCLUDE_SUBDOMAINS=(bool, False),
    SECURE_HSTS_PRELOAD=(bool, False),
    SESSION_COOKIE_SECURE=(bool, False),
    CSRF_COOKIE_SECURE=(bool, False),
    USE_X_FORWARDED_HOST=(bool, False),
    SECURE_PROXY_SSL_HEADER_ENABLED=(bool, False),
    ENABLE_DJANGO_EXTENSIONS=(bool, False),
    TIME_ZONE=(str, "America/Guayaquil"),
)
environ.Env.read_env(PROJECT_DIR / ".env")
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default=env("DJANGO_SECRET_KEY", default="unsafe-dev-key-change-me"))
DEBUG = env("DEBUG", default=env("DJANGO_DEBUG"))
ALLOWED_HOSTS = env("ALLOWED_HOSTS", default=env("DJANGO_ALLOWED_HOSTS"))
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS", default=env("DJANGO_CSRF_TRUSTED_ORIGINS"))

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "axes",
    "django_htmx",
    "rest_framework",
]

if env("ENABLE_DJANGO_EXTENSIONS"):
    THIRD_PARTY_APPS.append("django_extensions")

LOCAL_APPS = [
    "apps.core",
    "apps.parametros",
    "apps.zonas",
    "apps.iglesias",
    "apps.usuarios",
    "apps.miembros",
    "apps.familias",
    "apps.cargos",
    "apps.obreros",
    "apps.ministerios",
    "apps.escuela_dominical",
    "apps.asistencia",
    "apps.eventos",
    "apps.finanzas",
    "apps.aportes_nacionales",
    "apps.traslados",
    "apps.certificados",
    "apps.documentos",
    "apps.inventario",
    "apps.reportes",
    "apps.notificaciones",
    "apps.auditoria",
    "apps.api",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "axes.middleware.AxesMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default=env("POSTGRES_DB", default="sistema_iglesia")),
        "USER": env("DB_USER", default=env("POSTGRES_USER", default="sistema_iglesia_user")),
        "PASSWORD": env("DB_PASSWORD", default=env("POSTGRES_PASSWORD", default="sistema_iglesia_pass")),
        "HOST": env("DB_HOST", default=env("POSTGRES_HOST", default="db")),
        "PORT": env("DB_PORT", default=env("POSTGRES_PORT", default="5432")),
    }
}

AUTH_USER_MODEL = "usuarios.Usuario"
LOGIN_URL = "core:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "core:login"
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-ec"
TIME_ZONE = env("TIME_ZONE")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
if DEBUG:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_AGE = env("SESSION_COOKIE_AGE")
SESSION_COOKIE_NAME = env("SESSION_COOKIE_NAME", default="sistema_iglesia_sessionid")
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE")
CSRF_COOKIE_NAME = env("CSRF_COOKIE_NAME", default="sistema_iglesia_csrftoken")
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE")
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT")
SECURE_HSTS_SECONDS = env("SECURE_HSTS_SECONDS")
SECURE_HSTS_INCLUDE_SUBDOMAINS = env("SECURE_HSTS_INCLUDE_SUBDOMAINS")
SECURE_HSTS_PRELOAD = env("SECURE_HSTS_PRELOAD")
USE_X_FORWARDED_HOST = env("USE_X_FORWARDED_HOST")
if env("SECURE_PROXY_SSL_HEADER_ENABLED"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

AXES_FAILURE_LIMIT = env("AXES_FAILURE_LIMIT")
AXES_COOLOFF_TIME = env("AXES_COOLOFF_TIME")
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_RESET_ON_SUCCESS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

REDIS_URL = env("REDIS_URL", default="redis://redis:6379/0")
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://redis:6379/1")
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
