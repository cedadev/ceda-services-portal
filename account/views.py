""" Django app views module """

__author__ = "Rhys Evans"
__date__ = "2021-02-18"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"

import logging
import json
import random
import string
import base64
import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from crypto_cookie.encoding import Encoder

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Permission
from django.contrib.auth import login
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_safe
from django.shortcuts import render, redirect
from django.urls import reverse

from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework import exceptions
from rest_framework.response import Response as ApiResponse
from jasmin_services.models import Category, Service, Role, RoleObjectPermission, Request
from jasmin_metadata.models import Form

from .models import CEDAUser, AccessTokens
from .rabbit import RabbitConnection


LOG = logging.getLogger(__name__)


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

def _get_rabbit_producer_class():

    if hasattr(settings, "RABBIT_SERVER") \
            and "PRODUCER" in settings.RABBIT_SERVER:
        module_path, _, class_name = \
            settings.RABBIT_SERVER["PRODUCER"].rpartition(".")
        connector_module = __import__(module_path, fromlist=[class_name])
    else:
        return RabbitProducer

    return getattr(connector_module, class_name)

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

    if password:
        secret = base64.b64decode(settings.ENCRYPTION_KEY)
        token = Encoder().encode_msg(password, secret)
        message = {"username": request.user.username, "token": token}
        try:
            with RabbitConnection() as connection:
                connection.publish(message)
        except Exception as e:
            LOG.debug("Submission failed to submit")
            raise e

    return render(request, 'account/ftp_password.html', {
        'password' : password
    })

@require_http_methods(['GET', 'POST'])
@login_required
def access_token_generator(request):
    """
    Handler for ```/account/token```.

    Responds to GET requests only.

    Provides the page for generating an access token
    """
    error_details = request.session.pop("errors", None)

    user = CEDAUser.objects.filter(username = request.user.username)
    access_tokens = AccessTokens.objects.filter(user=user.first())

    return render(request, 'account/access_token.html', {"details": error_details, "token_list": access_tokens})

@require_http_methods(['POST'])
@login_required
def access_token_create(request):
    CEDAUser.objects.filter(username = request.user.username).update(has_access_token = True)

    # url = "https://accounts.ceda.ac.uk/realms/ceda/protocol/openid-connect/token"

    # payload = f'username={ request.user.username }&password={request.POST.get("password")}&client_id={settings.OIDC_RP_CLIENT_ID}&client_secret={settings.OIDC_RP_CLIENT_SECRET}&grant_type=password'
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = create_access_token(request.POST.get("password"), request.user.username)
    response_json = response.json()

    if response.status_code == 200:
        AccessTokens.objects.create(
            token=response_json["access_token"],
            user=CEDAUser.objects.filter(username = request.user.username).first()
        )

        return redirect(access_token_generator)
    else:
        errors = {
            "text": f"There was an issue with creating an access token: { response_json['error_description'] }. Please check your password and try again."
        }
        request.session['errors'] = errors
        return redirect(access_token_generator)

@require_http_methods(['POST'])
@login_required
def access_token_delete(request):
    response = delete_access_token(key=request.POST.get("key"))

    if response.status_code != 200:
        errors = {
            "text": "The token could not be deleted. We encountered the " + 
            f"following issue: {response.json()['error_description']}"
        }
        request.session['errors'] = errors
    return redirect(access_token_generator)


@api_view(["POST"])
def access_token_api_create(request):
    auth = request.META.get('HTTP_AUTHORIZATION', b'')

    auth = auth.split()

    if not auth or auth[0].lower() != 'basic':
        return None
    
    if len(auth) == 1:
        msg = 'Invalid basic header. No credentials provided.'
        raise exceptions.AuthenticationFailed(msg)
    elif len(auth) > 2:
        msg = 'Invalid basic header. Credentials string should not contain spaces.'
        raise exceptions.AuthenticationFailed(msg)

    try:
        try:
            auth_decoded = base64.b64decode(auth[1]).decode('utf-8')
        except UnicodeDecodeError:
            auth_decoded = base64.b64decode(auth[1]).decode('latin-1')
        auth_parts = auth_decoded.partition(':')
    except (TypeError, UnicodeDecodeError):
        msg = 'Invalid basic header. Credentials not correctly base64 encoded.'
        raise exceptions.AuthenticationFailed(msg)
    except Exception as e:
        msg = (e)
        raise exceptions.AuthenticationFailed(msg)

    userid, password = auth_parts[0], auth_parts[2]
    user = CEDAUser.objects.filter(username = userid).first()
    

    response = create_access_token(password, userid)
    response_json = response.json()
    
    api_response = {}
    if response.status_code == 200:
        AccessTokens.objects.create(
            token=response_json["access_token"],
            user=CEDAUser.objects.filter(username = userid).first()
        )
        api_response = {
            "access_token": response_json["access_token"]
        }
    else:
        api_response = response_json

    return ApiResponse(data=api_response) #, status_code=response.status_code)

@api_view(["POST"])
def access_token_api_delete(request):
    logging.error("started access")
    auth = request.META.get('HTTP_AUTHORIZATION', b'')

    auth = auth.split()

    if not auth or auth[0].lower() != 'basic':
        return None

    if len(auth) == 1:
        msg = 'Invalid basic header. No credentials provided.'
        raise exceptions.AuthenticationFailed(msg)
    elif len(auth) > 2:
        msg = 'Invalid basic header. Credentials string should not contain spaces.'
        raise exceptions.AuthenticationFailed(msg)

    try:
        try:
            auth_decoded = base64.b64decode(auth[1]).decode('utf-8')
        except UnicodeDecodeError:
            auth_decoded = base64.b64decode(auth[1]).decode('latin-1')
        auth_parts = auth_decoded.partition(':')
    except (TypeError, UnicodeDecodeError):
        msg = 'Invalid basic header. Credentials not correctly base64 encoded.'
        raise exceptions.AuthenticationFailed(msg)
    except Exception as e:
        msg = (e)
        raise exceptions.AuthenticationFailed(msg)
    
    userid, password = auth_parts[0], auth_parts[2]
    user = CEDAUser.objects.filter(username = userid)

    logging.error("fine here")
    # if not user:
    #     msg = 'Invalid password'
    #     raise exceptions.AuthenticationFailed(msg)
    
    find_token = AccessTokens.objects.filter(user=user[0], token=request.POST.get("token"))

    logging.error(find_token)
    if len(find_token) < 1:
        raise exceptions.NotFound("Could not find token")
    
    response = delete_access_token(token_name=request.POST.get("token"))

    if response.status_code == 200:
        api_response = {
                "deleted": True,
                "access_token": find_token[0].token
            }
        logging.error(response.status_code)
    else:
        api_response = {
            "status_code": response.status_code,
            "json": response.json()
        }

    return ApiResponse(data=api_response)

def create_access_token(password, username):
    url = "https://accounts.ceda.ac.uk/realms/ceda/protocol/openid-connect/token"

    payload = f'username={ username }&password={ password }&client_id={settings.OIDC_RP_CLIENT_ID}&client_secret={settings.OIDC_RP_CLIENT_SECRET}&grant_type=password'
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    
    return response

def delete_access_token(key=None, token_name=None):
    if key is not None:
        token = AccessTokens.objects.get(pk=key)
    elif token_name is not None:
        token = AccessTokens.objects.get(token=token_name)
    else:
        raise exceptions.APIException({"error": "Did not provide token details"}, code=400)

    url = "https://accounts.ceda.ac.uk/realms/ceda/protocol/openid-connect/revoke"
    payload = f'client_id={settings.OIDC_RP_CLIENT_ID}&client_secret={settings.OIDC_RP_CLIENT_SECRET}&token={token.token}'
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        token.delete()

    return response
