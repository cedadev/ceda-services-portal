__author__ = "Rhys Evans"
__date__ = "2021-02-18"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD-3-Clause"

import logging
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from ..models import AccessTokens, CEDAUser
from . import common

LOG = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
@login_required
def access_token_generator(request):
    """
    Handle ```/account/token```.

    Responds to GET requests only.

    Provides the page for generating an access token
    """
    error_details = request.session.pop("errors", None)

    user = CEDAUser.objects.filter(username=request.user.username)
    # Disable filtering by expiry for now, short expiry time makes testing annoying
    # access_tokens = AccessTokens.objects.filter(user=user.first(), expiry__gte=datetime.now())
    access_tokens = AccessTokens.objects.filter(user=user.first())

    return render(
        request,
        "account/access_token.html",
        {"details": error_details, "token_list": access_tokens},
    )


@require_http_methods(["POST"])
@login_required
def access_token_create(request):
    """View to allow users to create access token.

    Accepts a post request and returns the access token.
    """
    CEDAUser.objects.filter(username=request.user.username).update(
        has_access_token=True
    )

    # url = "https://accounts.ceda.ac.uk/realms/ceda/protocol/openid-connect/token"

    # payload = f'username={ request.user.username }&password={request.POST.get("password")}&client_id={settings.OIDC_RP_CLIENT_ID}&client_secret={settings.OIDC_RP_CLIENT_SECRET}&grant_type=password'
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = common.create_access_token(
        request.POST.get("password"), request.user.username
    )
    response_json = response.json()

    if response.status_code == 200:
        AccessTokens.objects.create(
            token=response_json["access_token"],
            user=CEDAUser.objects.filter(username=request.user.username).first(),
            expiry=timezone.now() + timedelta(seconds=response_json["expires_in"]),
            token_name=(
                request.POST.get("token_name")
                if request.POST.get("token_name") != ""
                else None
            ),
        )

        return redirect(access_token_generator)
    else:
        if (
            response.json().get("error_description")
            == "You may only have 2 access tokens"
        ):
            errors = {
                "text": f"There was an issue with creating an access token: { response_json['error_description'] }. Please delete an access token to create a new one."
            }
        else:
            errors = {
                "text": f"There was an issue with creating an access token: { response_json['error_description'] }. Please check your password and try again."
            }
        request.session["errors"] = errors
        return redirect(access_token_generator)


@require_http_methods(["POST"])
@login_required
def access_token_delete(request):
    """Allow user to delete their access token.

    Accepts a post request and deletes the token.
    """
    response = common.delete_access_token(key=request.POST.get("key"))

    if response.status_code != 200:
        errors = {
            "text": "The token could not be deleted. We encountered the "
            + f"following issue: {response.json()['error_description']}"
        }
        request.session["errors"] = errors
    return redirect(access_token_generator)
