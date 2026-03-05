from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv



# BASE_DIR
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde .env (solo en local)
load_dotenv(BASE_DIR / ".env")


# Entorno: 'production' en Heroku, 'development' en local
ENVIRONMENT = os.getenv('DJANGO_ENV', 'development')

#Default email SendGrid
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "cintainteligente@gmail.com")

# Configurar SECRET_KEY
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key')

# Configuración de DEBUG
DEBUG = ENVIRONMENT != 'production'

# Configuración de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'modulo_gestion_qr': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'storages': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'boto3': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'botocore': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Configurar ALLOWED_HOSTS
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'map-cintandina-ff394dd39613.herokuapp.com']
if ENVIRONMENT == 'production':
    ALLOWED_HOSTS.extend([
        'qr-sb.cintandina.com',
        'map-cintandina-ff394dd39613.herokuapp.com',
        '.herokuapp.com'
    ])

# Configurar URL para generar las url de los seriales
if ENVIRONMENT == 'production':
    BASE_URL = os.getenv('BASE_URL', 'https://qr-sb.cintandina.com')
else:
    BASE_URL = 'http://127.0.0.1:8000'

# Configurar CSRF
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000']
if ENVIRONMENT == 'production':
    CSRF_TRUSTED_ORIGINS += [
        'https://qr-sb.cintandina.com',
        'https://map-cintandina-ff394dd39613.herokuapp.com'
    ]


# Toggle para habilitar S3 (en local y prod)
#USE_S3 = os.getenv('USE_S3', '1') == '1'

USE_S3 = os.getenv('USE_S3', 'True') == 'True'

# Configuración de Amazon S3 para archivos multimedia
if USE_S3:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-2')

    # dominio regional (recomendado)
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'

    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_S3_SIGNATURE_VERSION = "s3v4"

    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'



# Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'modulo_gestion_qr.apps.ModuloGestionQrConfig',
    'compressor',
    'widget_tweaks',
    'storages',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]

# Configurar almacenamiento de archivos estáticos con Whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# URLs
ROOT_URLCONF = 'gestion_etiquetas_qr.urls'

# Configuración de plantillas
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

# WSGI
WSGI_APPLICATION = 'gestion_etiquetas_qr.wsgi.application'

# Configuración de base de datos
if ENVIRONMENT == 'production':
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, default=os.getenv('DATABASE_URL'))
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
           # 'ENGINE': 'django.db.backends.postgresql',
            #'NAME': 'gestion_etiquetas_qr',
            #'USER': 'postgres',
            #'PASSWORD': '2024',
            #'HOST': 'localhost',
            #'PORT': '5432',
        }
    }

# Validación de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Configuración de idioma y zona horaria
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Archivos estáticos
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Archivos multimedia (S3 reemplaza MEDIA_ROOT)
# MEDIA_URL ya está configurado para S3
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # Comentado, no necesario con S3

# Configuración de modelo de usuario
AUTH_USER_MODEL = 'modulo_gestion_qr.User'

# Tipo de clave primaria por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de login y logout
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


# settings.py

# Patrones que SÍ se mostrarán en el select del form (glob)
LANDING_TEMPLATE_PATTERNS = [
    'landing_cinta.html',      # landing.html, landing_cliente.html, landing_x.html, etc.
    'cliente_*.html',     # cliente_x.html
    'template_*.html',    # template_x.html (si los nombras así)
    'delmonte_landing1.html',
    'templateCintandina.html',
    'templateProducto1.html',
    'crear_solicitud.html',
    # Agrega más patrones si los usas: 'micliente/*.html', etc.
]

# Nombres (archivo base) que NO deben aparecer (exclusiones exactas)
LANDING_TEMPLATE_EXCLUDE = [
    '_base.html',
    'base.html',
    'login.html',
    'dashboard.html',
    'index.html',
    'crear_template_cliente.html',
    'listado_templates.html',
    #'crear_solicitud.html',
    'editar_solicitud.html',
    'buscar_solicitud.html',
    'ver_solicitud.html',
    'actualizar_seriales.html',
    'asociar_seriales.html',
    'buscar_seriales.html',
    'buscar_solicitud.html',
    'cliente_success.html',
    'crear_cliente.html',
    'crear_producto.html',
    #'crear_solicitud.html',
    'crear_template_cliente.html',
    'dashboard.html',
    'editar_solicitud.html',
    'generar_qr.html',
    'generar_seriales.html',
    'home.html',
    'informacion_qr.html',
    'listado_clientes.html',
    'listado_productos.html',
    'listado_templates.html',
    'login.html',
    'logout.html',
    'producto_success.html',
    'serial_success.html',
    'ver_seriales.html',
    'ver_solicitud.html',
    # agrega otros que no quieras mostrar
]

