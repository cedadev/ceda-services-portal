""" Django app views module """

__author__ = "Rhys Evans"
__date__ = "2021-02-18"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"

import logging
import json
import random
import string
from django.conf import settings
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_safe
from django.shortcuts import render, redirect
from django.urls import reverse

from rest_framework.views import APIView
from rest_framework.response import Response
from jasmin_services.models import Category, Service, Role, RoleObjectPermission, Request
from jasmin_metadata.models import Form

from .models import CEDAUser


class ServiceCreate(APIView):
    """
    List all snippets, or create a new snippet.
    """

    def get(self, request, *args, **kwargs):

        category = Category.objects.get(name=request.data["category"])

        name = request.data.get('name')
        summary = request.data.get('summary')
        hidden = request.data.get('hidden')
        service, created = Service.objects.get_or_create(
            category=category,
            name=name
        )
        if created:
            service.summary = summary
            service.hidden = hidden

            self.save_related(service)

            service.save()

        return Response({"message": f"Service {name} created"})

    def get_role_permissions(self):
        return (
            Permission.objects.get(
                content_type = ContentType.objects.get_for_model(Role),
                codename = 'view_users_role',
            ),
            Permission.objects.get(
                content_type = ContentType.objects.get_for_model(Role),
                codename = 'send_message_role',
            ),
            Permission.objects.get(
                content_type = ContentType.objects.get_for_model(Request),
                codename = 'decide_request',
            ),
        )

    def create_role_object_permissions(self, role, target_role):
        permissions = self.get_role_permissions()
        RoleObjectPermission.objects.bulk_create([
            RoleObjectPermission(
                role = role,
                permission =  permission,
                content_type = ContentType.objects.get_for_model(target_role),
                object_pk = target_role.pk
            )
            for permission in permissions
        ])

    def save_related(self, service):
        default_form = Form.objects.get(pk = settings.JASMIN_SERVICES['DEFAULT_METADATA_FORM'])
        # Create the three default roles
        user_role, _ = service.roles.get_or_create(
            name = 'USER',
            defaults = dict(
                description = 'Standard user role',
                hidden = False,
                position = 100,
                metadata_form = default_form
            )
        )
        deputy_role, _ = service.roles.get_or_create(
            name = 'DEPUTY',
            defaults = dict(
                description = 'Service deputy manager role',
                hidden = True,
                position = 200,
                metadata_form = default_form
            )
        )
        self.create_role_object_permissions(deputy_role, user_role)
        manager_role, _ = service.roles.get_or_create(
            name = 'MANAGER',
            defaults = dict(
                description = 'Service manager role',
                hidden = True,
                position = 300,
                metadata_form = default_form
            )
        )
        self.create_role_object_permissions(manager_role, user_role)
        self.create_role_object_permissions(manager_role, deputy_role)

"""
@api_view(['GET'])
def create_service(request):
    category = request.GET.get('category')
    category, _ = Category.objects.get_or_create(name=category)

    name = request.GET.get('name')
    summary = request.GET.get('summary')
    hidden = request.GET.get('hidden')
    service, created = Service.objects.get_or_create(
        category=category,
        name=name
    )
    if created:
        service.summary = summary
        service.hidden = hidden
        service.save()

    return Response({"message": f"Service {name} created"})
"""


@require_safe
@login_required
def jasmin_account(request):
    """
    Handler for ``/account/jasmin/``.

    Responds to GET requests only.

    Allows the user to link their JASMIN account or displays previously linked jasmin account.
    """
    return render(request, 'account/jasmin_account.html', {
        'jasmin_account' : settings.JASMIN_AUTH['JASMIN_ACCOUNT_URL']
    })


@require_safe
def account_jasmin_authorise(request):
    """
    Handler for ``/jasmin_authorise/``.

    Responds to GET requests only.

    Initiates the OAuth2 authorisation process with the JASMIN OAuth server.
    """
    # Reset any existing state in the session
    if 'oauth_state' in request.session:
        del request.session['oauth_state']
    # Generate a new state and the accompanying URL to use for authorisation
    jasmin_oauth = OAuth2Session(
        settings.JASMIN_AUTH['CLIENT_ID'],
        redirect_uri = settings.BASE_URL + reverse('jasmin_token_exchange'),
        scope = settings.JASMIN_AUTH['REQUIRED_SCOPES']
    )
    auth_url, state = jasmin_oauth.authorization_url(settings.JASMIN_AUTH['AUTH_URL'])
    # Keep the state for later
    request.session['oauth_state'] = state
    return redirect(auth_url)


@require_safe
def account_jasmin_token_exchange(request):
    """
    Handler for ``/jasmin_token_exchange/``.

    Responds to GET requests only.

    Handles the exchange of an authorisation grant code for an access token with
    the JASMIN OAuth server. The token is saved into the session.
    """
    # If we have not yet entered the OAuth flow, redirect to the start
    if 'oauth_state' not in request.session:
        return redirect('jasmin_authorise')
    # Notify the action of any errors
    if 'error' in request.GET:
        response = redirect('jasmin_link')
        response['Location'] += '?error={}'.format(request.GET['error'])
        return response
    # Exchange the grant code for a token
    # Store the token in the session for processing by the action view
    request.session['oauth_token'] = OAuth2Session(
        settings.JASMIN_AUTH['CLIENT_ID'],
        redirect_uri = settings.BASE_URL + reverse('jasmin_token_exchange'),
        scope = settings.JASMIN_AUTH['REQUIRED_SCOPES'],
        # The state is single use
        state = request.session.pop('oauth_state')
    ).fetch_token(
        settings.JASMIN_AUTH['TOKEN_URL'],
        client_secret = settings.JASMIN_AUTH['CLIENT_SECRET'],
        authorization_response = settings.BASE_URL + request.get_full_path(),
        verify = settings.JASMIN_AUTH['TLS_VERIFY']
    )

    # Redirect to the actual action
    return redirect('jasmin_link')


def _handle_oauth_error(request, redirect_to):
    error = request.GET['error']
    if error == 'access_denied':
        # If access was denied
        message = 'Access to JASMIN account was denied'
    else:
        message = 'Unable to authorise with JASMIN ({})'.format(error)
    messages.error(request, message)
    return redirect(redirect_to)


@require_safe
@login_required
def account_jasmin_link(request):
    """
    Handler for ``/jasmin_link/``.

    Responds to GET requests only. The user must be verified.

    Attempts to link the CEDA and JASMIN accounts.
    """
    # If the account is already linked with a JASMIN account, don't link again
    if request.user.jasminaccountid:
        messages.info(request, 'JASMIN account already linked')
        return redirect('jasmin_account')
    # If there was an error with the authorisation, report it
    if 'error' in request.GET:
        return _handle_oauth_error(request, 'jasmin_account')
    # Force the user to re-authorise with CEDA every time they access this URL
    # by only inspecting the token from the session
    # We also remove the token from the session as we consume it
    token = request.session.pop('oauth_token', None)
    if not token:
        return redirect('jasmin_authorise')
    # Configure requests-oauthlib session to automatically refresh expired tokens
    jasmin_oauth = OAuth2Session(
        settings.JASMIN_AUTH['CLIENT_ID'],
        token = token,
        auto_refresh_url = settings.JASMIN_AUTH['TOKEN_URL'],
        auto_refresh_kwargs = {
            'client_id' : settings.JASMIN_AUTH['CLIENT_ID'],
            'client_secret' : settings.JASMIN_AUTH['CLIENT_SECRET'],
        },
        # Update the local token with the new token if it is refreshed
        token_updater = lambda t: token.update(t)
    )
    try:
        response = jasmin_oauth.get(
            settings.JASMIN_AUTH['LINK_URL'],
            verify = settings.JASMIN_AUTH['TLS_VERIFY']
        )
    except InvalidGrantError:
        # If the grant is invalid, redirect to jasmin_authorise
        # Note that the token is already removed from the session
        return redirect('jasmin_authorise')
    if response.status_code == 200:
        # If the account linking was successful, store the OAuth token for later
        content = json.loads(response.content)
        CEDAUser.objects.filter(username = request.user.username).update(jasminaccountid = content['username'])
        messages.success(request, 'JASMIN account linked successfully')
    else:
        try:
            # If we can extract an error message from an error response, then just
            # report it to the user
            messages.error(request, response.json()['error_message'])
        except Exception:
            # If we can't extract an error message from the error response, it might
            # be something more serious, so log it
            _log.error('Error while linking JASMIN account to {}: {} {}'.format(
                request.user, response.status_code, response.reason
            ))
            messages.error(request, 'Error while linking JASMIN account')
    return redirect('jasmin_account')


@require_http_methods(['GET', 'POST'])
@login_required
def account_ftp_password(request):
    """
    Handler for ``/account/ftp/``.

    Responds to GET requests only.

    Allows the user to create or reset their ftp password.
    """
    # Create new ftp password.
    if request.method == 'POST':
        CEDAUser.objects.filter(username = request.user.username).update(has_ftp_password = True)
        password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=12))
    else:
        password = None
    
    return render(request, 'account/ftp_password.html', {
        'password' : password
    })
