from django.conf import settings
from django.contrib import auth
from django.http import request, HttpResponseRedirect

from mozilla_django_oidc.utils import is_authenticated

def keycloak_logout(request):
    '''
    Perform the logout of the app and redirect to keycloak
    '''

    if is_authenticated(request.user):
        logout_url = settings.OIDC_OP_LOGOUT_ENDPOINT + "?redirect_uri=" + request.build_absolute_uri(settings.LOGOUT_REDIRECT_URL)

        # Log out the Django user if they were logged in.
        auth.logout(request)

        return HttpResponseRedirect(logout_url)

def keycloak_account(request):
    '''
    Perform redirect to keycloak account
    '''

    return HttpResponseRedirect(settings.OIDC_OP_ACCOUNT_ENDPOINT)
