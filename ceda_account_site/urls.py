""" URL Configuration for the site. """

__author__ = "William Tucker"
__date__ = "2019-08-28"
__copyright__ = "Copyright 2019 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level directory"


from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('', include('ceda_account.urls')),

    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('services/', include('ceda_services.urls')),
]
