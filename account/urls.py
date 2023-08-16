""" Django app urls module """

__author__ = "William Tucker"
__date__ = "2021-02-18"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"


from django.urls import include, path
from . import views



urlpatterns = [
    path('service/create/', views.ServiceCreate.as_view()),
    path('account/', include([
            path('jasmin/', views.jasmin_account, name='jasmin_account'),
            path('jasmin_authorise/', views.account_jasmin_authorise, name = 'jasmin_authorise'),
            path('jasmin_token_exchange/', views.account_jasmin_token_exchange, name = 'jasmin_token_exchange'),
            path('jasmin_link/', views.account_jasmin_link, name = 'jasmin_link'),
            path('ftp/', views.account_ftp_password, name = 'ftp_password'),
            path('token/', views.access_token_generator, name = 'access_token'),
            path('token/create/', views.access_token_create, name = 'access_token_create'),
            path('token/delete/', views.access_token_delete, name = 'access_token_delete'),
        ],),
    ),
]