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
from ..utils import keycloak_apply_globus_link

LOG = logging.getLogger(__name__)


def _handle_oauth_error(request, redirect_to):
    error = request.GET["error"]
    if error == "access_denied":
        # If access was denied
        message = "Access to GLOBUS account was denied"
    else:
        message = f"Unable to authorise with GLOBUS ({error})"
    messages.error(request, message)
    return redirect(redirect_to)


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


@require_safe
def account_globus_authorise(request):
    """
    Handle ``/globus_authorise/``.

    Responds to GET requests only.

    Initiates the OAuth2 authorisation process with the GLOBUS OAuth server.
    """
    request.session.pop("globus_oauth_state", None)

    globus_oauth = OAuth2Session(
        settings.GLOBUS_AUTH["CLIENT_ID"],
        redirect_uri=settings.BASE_URL + reverse("globus_token_exchange"),
        scope=settings.GLOBUS_AUTH["REQUIRED_SCOPES"],
    )

    auth_url, state = globus_oauth.authorization_url(
        settings.GLOBUS_AUTH["AUTH_URL"]
    )

    request.session["globus_oauth_state"] = state
    return redirect(auth_url)

@require_safe
def account_globus_token_exchange(request):
    """
    Handle ``/globus_token_exchange/``.

    Responds to GET requests only.

    Handles the exchange of an authorisation grant code for an access token with
    the GLOBUS OAuth server. The token is saved into the session.
    """
    state = request.session.pop("globus_oauth_state", None)

    if not state:
        return redirect("globus_authorise")

    if "error" in request.GET:
        return redirect(
            f"{reverse('globus_link')}?error="
            f"{request.GET['error']}"
        )

    globus_oauth = OAuth2Session(
        settings.GLOBUS_AUTH["CLIENT_ID"],
        redirect_uri=settings.BASE_URL + reverse("globus_token_exchange"),
        scope=settings.GLOBUS_AUTH["REQUIRED_SCOPES"],
        state=state,
    )

    try:
        token = globus_oauth.fetch_token(
            settings.GLOBUS_AUTH["TOKEN_URL"],
            client_secret=settings.GLOBUS_AUTH["CLIENT_SECRET"],
            authorization_response=settings.BASE_URL + request.get_full_path(),
            verify=settings.GLOBUS_AUTH["TLS_VERIFY"],
        )
    except Exception:
        LOG.exception("Error exchanging Globus authorisation code")
        messages.error(request, "Unable to authorise with GLOBUS")
        return redirect("globus_account")

    request.session["globus_oauth_token"] = token
    return redirect("globus_link")


@require_safe
@login_required
def account_globus_link(request):
    """
    Handle ``/globus_link/``.

    Responds to GET requests only. The user must be verified.

    Attempts to link the CEDA and GLOBUS accounts.
    """
    # If the account is already linked with a GLOBUS account, don't link again
    if request.user.globusaccountid:
        messages.info(request, "GLOBUS account already linked")
        return redirect("globus_account")
    # If there was an error with the authorisation, report it
    if "error" in request.GET:
        return _handle_oauth_error(request, "globus_account")
    # Force the user to re-authorise with CEDA every time they access this URL
    # by only inspecting the token from the session
    # We also remove the token from the session as we consume it
    token = request.session.pop("globus_oauth_token", None)

    if not token:
        return redirect("globus_authorise")

    globus_oauth = OAuth2Session(
        settings.GLOBUS_AUTH["CLIENT_ID"],
        token=token,
    )

    try:
        response = globus_oauth.get(
            settings.GLOBUS_AUTH["USERINFO_URL"],
            verify=settings.GLOBUS_AUTH["TLS_VERIFY"],
            timeout=10,
        )
        response.raise_for_status()
        globus_user = response.json()
        globusaccountid = globus_user["sub"]

        keycloak_apply_globus_link(request.user, globusaccountid)

        CEDAUser.objects.filter(
            username=request.user.username
        ).update(globusaccountid=globusaccountid)

        messages.success(request, "GLOBUS account linked successfully")

    except Exception:
        LOG.exception(
            "Error while linking GLOBUS account to %s",
            request.user,
        )
        messages.error(request, "Error while linking GLOBUS account")

    return redirect("globus_account")