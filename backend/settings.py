from pathlib import Path
import os

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-8&ar7635wwt_nzoz#)3eh&97!v=birf-g7^f+b+8_#m#(f#-72')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'hotel-management-backend-nu99.onrender.com',
    os.environ.get('PYTHONANYWHERE_HOST', ''),
]

# ── Jazzmin Admin UI ──────────────────────────────────────────────────────────
JAZZMIN_SETTINGS = {
    "site_title": "The HMS",
    "site_header": "The HMS",
    "site_brand": "✦ The HMS",
    "welcome_sign": "Hotel Management System — Admin Portal",
    "copyright": "© 2025 The HMS",

    "site_logo": None,
    "site_icon": None,
    "login_logo": None,
    "login_logo_dark": None,

    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "View Site", "url": "/", "new_window": True},
        {"name": "Bookings", "model": "myapp.booking"},
        {"name": "Guests", "model": "myapp.guest"},
    ],

    "usermenu_links": [
        {"name": "View Site", "url": "/", "new_window": True},
        {"model": "auth.user"},
    ],

    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],

    "icons": {
        "auth":                       "fas fa-shield-alt",
        "auth.user":                  "fas fa-user-circle",
        "auth.Group":                 "fas fa-layer-group",
        "myapp.User":                 "fas fa-hotel",
        "myapp.Room":                 "fas fa-bed",
        "myapp.Booking":              "fas fa-calendar-check",
        "myapp.Guest":                "fas fa-user-friends",
        "myapp.Employee":             "fas fa-user-tie",
        "myapp.Inventory":            "fas fa-boxes",
        "myapp.InventoryRequest":     "fas fa-clipboard-list",
        "myapp.Item":                 "fas fa-utensils",
        "myapp.Order":                "fas fa-shopping-bag",
        "myapp.Payment":              "fas fa-credit-card",
        "myapp.Invoice":              "fas fa-file-invoice-dollar",
        "myapp.Housekeeping":         "fas fa-broom",
        "myapp.PaymentGatewayConfig": "fas fa-cogs",
        "myapp.OTAChannelConfig":     "fas fa-plug",
        "myapp.HousekeepingAssignment": "fas fa-tasks",
        "myapp.SpecialRequest":       "fas fa-concierge-bell",
        "myapp.LostFound":            "fas fa-search",
        "myapp.Linen":                "fas fa-tshirt",
        "myapp.Notification":         "fas fa-bell",
        "myapp.Attendance":           "fas fa-clock",
        "myapp.Shift":                "fas fa-calendar-alt",
        "myapp.Leave":                "fas fa-umbrella-beach",
    },
    "default_icon_parents": "fas fa-chevron-right",
    "default_icon_children": "fas fa-dot-circle",

    "related_modal_active": True,
    "custom_css": "admin/css/custom_admin.css",
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,

    "search_model": ["myapp.User", "myapp.Booking", "myapp.Guest", "myapp.Room"],

    "order_with_respect_to": [
        "myapp",
        "myapp.User",
        "myapp.Room",
        "myapp.Booking",
        "myapp.Guest",
        "myapp.Employee",
        "myapp.Inventory",
        "myapp.InventoryRequest",
        "myapp.Item",
        "myapp.Order",
        "myapp.Payment",
        "myapp.Invoice",
        "myapp.Housekeeping",
        "myapp.PaymentGatewayConfig",
        "myapp.OTAChannelConfig",
    ],

    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": True,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-warning",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-warning",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "slate",
    "dark_mode_theme": "slate",
    "button_classes": {
        "primary":   "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info":      "btn-outline-info",
        "warning":   "btn-warning",
        "danger":    "btn-outline-danger",
        "success":   "btn-outline-success",
    },
    "actions_sticky_top": True,
}
# ─────────────────────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'myapp',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = False


# ✅ FIXED SECTION STARTS HERE
def clean_origin(url):
    return url.rstrip("/") if url else url


FRONTEND_URL = clean_origin(os.environ.get("FRONTEND_URL"))

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

if FRONTEND_URL:
    CORS_ALLOWED_ORIGINS.append(FRONTEND_URL)

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "https://hotel-management-one-zeta.vercel.app",
]

if FRONTEND_URL:
    CSRF_TRUSTED_ORIGINS.append(FRONTEND_URL)

if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    CSRF_TRUSTED_ORIGINS.append(
        f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}"
    )
# ✅ FIXED SECTION ENDS HERE


CORS_ALLOW_CREDENTIALS = True


ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'


import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from django.db import connections

_db_url = os.environ.get("DATABASE_URL")

if not _db_url:
    raise ImproperlyConfigured(
        "❌ DATABASE_URL is not set. Supabase/Postgres connection required."
    )

DATABASES = {
    "default": dj_database_url.parse(
        _db_url,
        conn_max_age=600,
        ssl_require=True,
    )
}

try:
    connections["default"].cursor()
    print("✅ Database connected successfully")
except Exception as e:
    raise ImproperlyConfigured(f"❌ Database connection failed: {e}")


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

SESSION_COOKIE_AGE = 30 * 24 * 60 * 60

SESSION_COOKIE_SECURE = True
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

AUTH_USER_MODEL = "myapp.User"
APPEND_SLASH = False

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'sijanofficial1@gmail.com'
EMAIL_HOST_PASSWORD = 'ktxm ggvn bqpk ujay'

KHALTI_SECRET_KEY = os.environ.get('KHALTI_SECRET_KEY', '2f2766ead6dd4866ac3b0ce0be469801')

FIELD_ENCRYPTION_KEY = os.environ.get(
    'FIELD_ENCRYPTION_KEY',
    'Jz5oW6gqBNEqoVl14BDGSj5H6u4YI36jUOiG7eEsGms='
)