"""
Django settings for celerycrawler project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ua$=!zpmt&@_=paocb_d_hxg78kdmxu3%f$e&15_eecg%k-2uv'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djcelery',
    'celerycrawler'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'celerycrawler.urls'

WSGI_APPLICATION = 'celerycrawler.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

########################
# celery configuration #
########################

import djcelery
djcelery.setup_loader()
BROKER_BACKEND = "couchdb"
BROKER_HOST = "localhost"
BROKER_PORT = 5984
BROKER_VHOST = "celerycrawler"

#BROKER_URL = 'amqp://guest:guest@localhost:5672'

CELERYD_CONCURRENCY = 5
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
CELERY_QUEUES = {"retrieve": {"exchange": "default",
                              "exchange_type": "direct",
                              "routing_key": "retrieve"},
                 "process": {"exchange": "default",
                             "exchange_type": "direct",
                             "routing_key": "process "},
                 "celery": {"exchange": "default",
                            "exchange_type": "direct",
                            "routing_key": "celery"}}


class Router(object):
    def route_for_task(self, task, args=None, kwargs=None):
        if task == "celerycrawler.tasks.retrieve_page":
            return { "queue": "retrieve" }
        else:
            return { "queue": "process" }

CELERY_ROUTES = (Router(), )

import couchdb

server = couchdb.Server()
try:
    db = server.create("celerycrawler")
except:
    db = server["celerycrawler"]

USER_AGENT = 'ua'
