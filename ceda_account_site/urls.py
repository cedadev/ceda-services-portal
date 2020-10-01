""" URL Configuration for the site. """

__author__ = "William Tucker"
__date__ = "2019-08-28"
__copyright__ = "Copyright 2019 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level directory"


from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('logout', views.keycloak_logout, name='logout'),
    path('account', views.keycloak_account, name='account'),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('services/', include('jasmin_services.urls', namespace = 'services')),
    path('notifications/', include('jasmin_notifications.urls', namespace = 'notifications')),
]
