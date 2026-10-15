import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_safe
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from requests_oauthlib import OAuth2Session

from ..models import CEDAUser
from ..utils import keycloak_apply_jasmin_link

LOG = logging.getLogger(__name__)



@require_safe
@login_required
def globus_account(request):
    """
    Handle ``/account/globus/``.

    Responds to GET requests only.

    Allows the user to link their GLOBUS account or displays previously linked globus account.
    """
    return render(
        request,
        "account/globus_account.html",
        {"globus_account": settings.GLOBUS_AUTH["GLOBUS_ACCOUNT_URL"]},
    )