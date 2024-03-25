""" URL Configuration for the site. """

__author__ = "William Tucker"
__date__ = "2019-08-28"
__copyright__ = "Copyright 2019 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level directory"


from django.contrib import admin
from django.shortcuts import HttpResponse
from django.urls import include, path
from django.views.generic.base import RedirectView

import account.views


def health_view(request):
    return HttpResponse("OK")


urlpatterns = [
    path("", RedirectView.as_view(url="services"), name="portal_root"),
    path("", include("account.urls")),
    path("health/", health_view, name="health"),
    path("admin/", admin.site.urls),
    path("oidc/", include("mozilla_django_oidc.urls")),
    path(
        "notifications/",
        include("jasmin_notifications.urls", namespace="notifications"),
    ),
    path("api-auth/", include("rest_framework.urls")),
    # Override some views from jasmin-services:
    path(
        "services/",
        include(
            [
                path(
                    "<slug:category>/<slug:service>/apply/<slug:role>/",
                    account.views.CEDARoleApplyView.as_view(),
                    name="role_apply",
                ),
                path(
                    "<slug:category>/<slug:service>/apply/<slug:role>/<int:bool_grant>/<int:previous>/",
                    account.views.CEDARoleApplyView.as_view(),
                    name="role_apply",
                ),
            ]
        ),
    ),
    # Then fall-through to the views from jasmin-services itself.
    path("services/", include("jasmin_services.urls", namespace="services")),
]
