from datetime import timedelta
from environs import Env
from pathlib import Path
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


BASE_DIR = Path(__file__).resolve().parent.parent

env = Env()
env.read_env()


SECRET_KEY = env.str("SECRET_KEY")

DEBUG = env.bool("DEBUG")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.import_export",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "import_export",
    "restaurant_app.apps.RestaurantAppConfig",
    "delivery_drivers.apps.DeliveryDriversConfig",
    "transactions_app.apps.TransactionsAppConfig",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # "DEFAULT_THROTTLE_CLASSES": [
    #     "rest_framework.throttling.UserRateThrottle",
    # ],
    # "DEFAULT_THROTTLE_RATES": {
    #     "user": "1000/day",
    # },
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "EXCEPTION_HANDLER": "restaurant_app.exceptions.custom_exception_handler",
}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")

CORS_ALLOW_CREDENTIALS = True

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "restaurant_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ['templates'],
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

WSGI_APPLICATION = "restaurant_project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Qatar"

USE_I18N = True

USE_TZ = False


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "restaurant_app.User"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=3),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(hours=24),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=3),
}

TWILIO_ACCOUNT_SID = env.str("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = env.str("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = env.str("TWILIO_PHONE_NUMBER")

UNFOLD = {
    "SITE_TITLE": "Nasscript",
    "SITE_HEADER": "Nasscript",
    "SITE_URL": "/admin",
    "SITE_ICON": lambda request: static("images/nasscript_logo.png"),
    "SITE_ICON": {
        "light": lambda request: static("images/nasscript_logo.png"),  # light mode
        "dark": lambda request: static("images/nasscript_logo.png"),  # dark mode
    },
    "SITE_LOGO": {
        "light": lambda request: static(
            "images/nasscript_full_banner_logo.png"
        ),  # light mode
        "dark": lambda request: static(
            "images/dark_logo.jpeg"
        ),  # dark mode
    },
    "SITE_SYMBOL": "restaurant",
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda request: static("images/nasscript_logo.png"),
        },
    ],
    "SHOW_HISTORY": False,
    "SHOW_VIEW_ON_SITE": True,
    "LOGIN": {
        "image": lambda request: static("images/nasscript_logo.png"),
        "redirect_after": lambda request: reverse_lazy(
            "admin:restaurant_app_user_changelist"
        ),
    },
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "fr": "🇫🇷",
                "nl": "🇧🇪",
            },
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("Developer Options"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Sidebar control"),
                        "icon": "room_service",
                        "link": reverse_lazy("admin:restaurant_app_sidebaritem_changelist"),
                    },
                    {
                        "title": _("Company Details"),
                        "icon": "room_service",
                        "link": reverse_lazy("admin:restaurant_app_logoinfo_changelist"),
                    },
                ],
            },
            {
                "title": _("Core"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Users"),
                        "icon": "people",
                        "link": reverse_lazy("admin:restaurant_app_user_changelist"),
                    },
                    {
                        "title": _("Customer Details"),
                        "icon": "people",
                        "link": reverse_lazy("admin:restaurant_app_customerdetails_changelist"),
                    },
                    {
                        "title": _("Credit Users"),
                        "icon": "credit_card",
                        "link": reverse_lazy(
                            "admin:restaurant_app_credituser_changelist"
                        ),
                    },
                    {
                        "title": _("Delivery Drivers"),
                        "icon": "directions_bike",
                        "link": reverse_lazy(
                            "admin:delivery_drivers_deliverydriver_changelist"
                        ),
                    },
                    {
                        "title": _("Categories"),
                        "icon": "category",
                        "link": reverse_lazy(
                            "admin:restaurant_app_category_changelist"
                        ),
                    },
                    {
                        "title": _("Dishes"),
                        "icon": "lunch_dining",
                        "link": reverse_lazy("admin:restaurant_app_dish_changelist"),
                    },
                                        {
                        "title": _("Dishes Sizes"),
                        "icon": "lunch_dining",
                        "link": reverse_lazy("admin:restaurant_app_dishsize_changelist"),
                    },
                    {
                        "title": _("Dish Varients"),
                        "icon": "format_list_bulleted",
                        "link": reverse_lazy("admin:restaurant_app_dishvariant_changelist"),
                    },
                    {
                        "title": _("Bills"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:restaurant_app_bill_changelist"),
                    },
                ],
            },
            {
                "title": _("Orders"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Orders"),
                        "icon": "shopping_cart",
                        "link": reverse_lazy("admin:restaurant_app_order_changelist"),
                    },
                                        {
                        "title": _("Online ThirdParty Order"),
                        "icon": "shopping_cart",
                        "link": reverse_lazy("admin:restaurant_app_onlineorder_changelist"),
                    },
                    {
                        "title": _("Order Items"),
                        "icon": "inventory_2",
                        "link": reverse_lazy(
                            "admin:restaurant_app_orderitem_changelist"
                        ),
                    },
                    {
                        "title": _("Credit Orders"),
                        "icon": "credit_score",
                        "link": reverse_lazy(
                            "admin:restaurant_app_creditorder_changelist"
                        ),
                    },
                    {
                        "title": _("Delivery Orders"),
                        "icon": "local_shipping",
                        "link": reverse_lazy(
                            "admin:delivery_drivers_deliveryorder_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("Chairs"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Chairs"),
                        "icon": "chair",
                        "link": reverse_lazy("admin:restaurant_app_chairs_changelist"),
                    },
                ],
            },
            {
                "title": _("FOC Products"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("FOC Products Management"),
                        "icon": "lunch_dining",
                        "link": reverse_lazy("admin:restaurant_app_focproduct_changelist"),
                    },
                ],
            },
            {
                "title": _("Mess"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Mess"),
                        "icon": "room_service",
                        "link": reverse_lazy("admin:restaurant_app_mess_changelist"),
                    },
                    {
                        "title": _("Mess Types"),
                        "icon": "handyman",
                        "link": reverse_lazy(
                            "admin:restaurant_app_messtype_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("Mess Menu"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Menu"),
                        "icon": "menu_book",
                        "link": reverse_lazy("admin:restaurant_app_menu_changelist"),
                    },
                    {
                        "title": _("Menu Items"),
                        "icon": "list",
                        "link": reverse_lazy(
                            "admin:restaurant_app_menuitem_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("Accounts"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Nature of Groups"),
                        "icon": "menu_book",
                        "link": reverse_lazy("admin:transactions_app_naturegroup_changelist"),
                    },
                    {
                        "title": _("Main Groups"),
                        "icon": "list",
                        "link": reverse_lazy(
                            "admin:transactions_app_maingroup_changelist"
                        ),
                    },
                    {
                        "title": _("Ledgers"),
                        "icon": "list",
                        "link": reverse_lazy(
                            "admin:transactions_app_ledger_changelist"
                        ),
                    },
                    {
                        "title": _("Transactions"),
                        "icon": "list",
                        "link": reverse_lazy(
                            "admin:transactions_app_transaction_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("Profit & Loss Share Transactions"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("ShareUsers"),
                        "icon": "menu_book",
                        "link": reverse_lazy("admin:transactions_app_shareusers_changelist"),
                    },
                    {
                        "title": _("Profit LossShare Transactions"),
                        "icon": "list",
                        "link": reverse_lazy(
                            "admin:transactions_app_profitlosssharetransaction_changelist"
                        ),
                    },
                    {
                        "title": _("Share User Transactions"),
                        "icon": "list",
                        "link": reverse_lazy(
                            "admin:transactions_app_shareusertransaction_changelist"
                        ),
                    },

                ],
            },
            {
                "title": _("Cash Count Sheet "),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Cash Count Sheet"),
                        "icon": "list",
                        "link": reverse_lazy(
                            "admin:transactions_app_cashcountsheet_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("Others"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Floors"),
                        "icon": "floor",
                        "link": reverse_lazy("admin:restaurant_app_floor_changelist"),
                    },
                    {
                        "title": _("Tables"),
                        "icon": "table_bar",
                        "link": reverse_lazy("admin:restaurant_app_table_changelist"),
                    },
                    {
                        "title": _("Coupons"),
                        "icon": "redeem",
                        "link": reverse_lazy("admin:restaurant_app_coupon_changelist"),
                    },
                ],
            },
        ],
    },
    "TABS": [
        {
            "models": [
                "restaurant_app.user",
            ],
            "items": [
                {
                    "title": _("Users"),
                    "link": reverse_lazy("admin:restaurant_app_user_changelist"),
                },
            ],
        },
    ],
}