""" Template context processors for this app """

__author__ = "William Tucker"
__date__ = "2021-02-17"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"


from django.conf import settings


def account_management_url(request):
   return {'account_management_url': settings.ACCOUNT_MANAGEMENT_URL}
