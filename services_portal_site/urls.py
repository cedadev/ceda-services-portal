""" URL Configuration for the site. """

__author__ = "William Tucker"
__date__ = "2019-08-28"
__copyright__ = "Copyright 2019 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level directory"


from django.contrib import admin
from django.shortcuts import HttpResponse
from django.urls import include, path


def health_view(request):
    return HttpResponse("OK")


urlpatterns = [
    path("health/", health_view, name="health"),
    path("admin/", admin.site.urls),
    path("oidc/", include("mozilla_django_oidc.urls")),
    path("services/", include("jasmin_services.urls", namespace="services")),
    path("notifications/", include("jasmin_notifications.urls",
                                   namespace="notifications")),
    path('api/v1/', include('account.urls')),
    path('api-auth/', include('rest_framework.urls')),
]
