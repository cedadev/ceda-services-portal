""" URL configuration for the ceda_account app. """

__author__ = "William Tucker"
__date__ = "2019-08-28"
__copyright__ = "Copyright 2019 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level directory"


from django.urls import path, re_path
from django.views.generic.base import RedirectView

from .views import ProfileView


urlpatterns = [
    path('', RedirectView.as_view(pattern_name='profile')),
    path('accounts/profile/', ProfileView.as_view(), name='profile'),
]
