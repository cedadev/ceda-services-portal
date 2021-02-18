""" Django app urls module """

__author__ = "William Tucker"
__date__ = "2021-02-18"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"


from django.urls import path
from . import views


urlpatterns = [
    path('service/create/', views.create_service),
]