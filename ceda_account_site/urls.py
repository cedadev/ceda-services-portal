""" URL Configuration for the site. """

__author__ = "William Tucker"
__date__ = "2019-08-28"
__copyright__ = "Copyright 2019 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level directory"


from django.contrib import admin
from django.urls import include, path
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('oidc_auth.urls')),
    path('services/', include('jasmin_services.urls', namespace = 'services')),
    path('notifications/', include('jasmin_notifications.urls', namespace = 'notifications')),
]
