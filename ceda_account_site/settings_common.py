""" Common settings for the site. """

__author__ = "William Tucker"
__date__ = "2019-08-28"
__copyright__ = "Copyright 2019 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level directory"


import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'markdown_deux',
    'ceda_account',
    'cookielaw',
    'fwtheme_django_ceda_serv',
    'fwtheme_django',
    'crispy_forms',
    'dateutil',
    'jasmin_ldap',
    'jasmin_ldap_django',
    'jasmin_django_utils',
    'jasmin_notifications',
    'jasmin_services',
    'jasmin_metadata',
    'django_countries',
    'bootstrap3',
    'widget_tweaks',
    'polymorphic',
    # Add social auth provider apps here:
    # e.g. 'allauth.socialaccount.providers.github',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'oidc_auth.middleware.SessionRefresh',
]

ROOT_URLCONF = 'ceda_account_site.urls'

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


AUTHENTICATION_BACKENDS = [
    'ceda_account.backends.CEDAAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

WSGI_APPLICATION = 'ceda_account_site.wsgi.application'


# Crispy forms

CRISPY_TEMPLATE_PACK = 'bootstrap4'
