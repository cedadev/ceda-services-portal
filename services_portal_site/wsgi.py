"""
WSGI config for services_portal_site project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

__author__ = "William Tucker"
__date__ = "2019-08-28"
__copyright__ = "Copyright 2019 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level directory"


import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'services_portal_site.settings')

application = get_wsgi_application()
