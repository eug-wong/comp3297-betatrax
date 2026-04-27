from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-n)ti$svy6%0mlw&i#^o_@(wn52$bil+sct00brj^&4yu_ov#8n'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver', '.localhost'] # 允許子網域

# --- Multi-tenancy 配置 ---

# Shared Apps: 存放租戶資訊（Client/Domain）和 Django 核心功能
SHARED_APPS = (
    'django_tenants',  # 必須放在第一位
    'customers',       # 你需要建立這個新 app 來管理租戶
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'drf_spectacular',
)

# Tenant Apps: 每個租戶專屬的業務資料
TENANT_APPS = (
    'django.contrib.auth', # 如果每個租戶有獨立用戶
    'rest_framework',
    'rest_framework.authtoken',
    'defects.apps.DefectsConfig', # 你的核心業務放在這裡
)

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

TENANT_MODEL = 'customers.Client' # 稍後建立
TENANT_DOMAIN_MODEL = 'customers.Domain' # 稍後建立

# -----------------------

MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware', # 必須放在最上方
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Betatrax API',
    'DESCRIPTION': 'API documentation for the Betatrax defect tracking system.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

ROOT_URLCONF = 'betatrax.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'betatrax.wsgi.application'

# 資料庫改用 django_tenants 的後端
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend', 
        'NAME': 'betatrax',                        
        'USER': 'comp3297',                         
        'PASSWORD': 'softengg',                    
        'HOST': 'localhost',                       
        'PORT': '',                              
    }
}

DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
LOGIN_REDIRECT_URL = '/api/defects/'
LOGOUT_REDIRECT_URL = '/api-auth/login/'