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
    # Reset any existing state in the session
    if "oauth_state" in request.session:
        del request.session["oauth_state"]
    # Generate a new state and the accompanying URL to use for authorisation
    globus_oauth = OAuth2Session(
        settings.GLOBUS_AUTH["CLIENT_ID"],
        redirect_uri=settings.BASE_URL + reverse("globus_token_exchange"),
        scope=settings.GLOBUS_AUTH["REQUIRED_SCOPES"],
    )
    auth_url, state = globus_oauth.authorization_url(settings.GLOBUS_AUTH["AUTH_URL"])
    # Keep the state for later
    request.session["oauth_state"] = state
    return redirect(auth_url)


@require_safe
def account_globus_token_exchange(request):
    """
    Handle ``/globus_token_exchange/``.

    Responds to GET requests only.

    Handles the exchange of an authorisation grant code for an access token with
    the GLOBUS OAuth server. The token is saved into the session.
    """
    # If we have not yet entered the OAuth flow, redirect to the start
    if "oauth_state" not in request.session:
        return redirect("globus_authorise")
    # Notify the action of any errors
    if "error" in request.GET:
        response = redirect("globus_link")
        response["Location"] += f"?error={request.GET['error']}"
        return response
    # Exchange the grant code for a token
    # Store the token in the session for processing by the action view
    request.session["oauth_token"] = OAuth2Session(
        settings.GLOBUS_AUTH["CLIENT_ID"],
        redirect_uri=settings.BASE_URL + reverse("globus_token_exchange"),
        scope=settings.GLOBUS_AUTH["REQUIRED_SCOPES"],
        # The state is single use
        state=request.session.pop("oauth_state"),
    ).fetch_token(
        settings.GLOBUS_AUTH["TOKEN_URL"],
        client_secret=settings.GLOBUS_AUTH["CLIENT_SECRET"],
        authorization_response=settings.BASE_URL + request.get_full_path(),
        verify=settings.GLOBUS_AUTH["TLS_VERIFY"],
    )

    # Redirect to the actual action
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
    token = request.session.pop("oauth_token", None)
    if not token:
        return redirect("globus_authorise")
    # Configure requests-oauthlib session to automatically refresh expired tokens
    globus_oauth = OAuth2Session(
        settings.GLOBUS_AUTH["CLIENT_ID"],
        token=token,
        auto_refresh_url=settings.GLOBUS_AUTH["TOKEN_URL"],
        auto_refresh_kwargs={
            "client_id": settings.GLOBUS_AUTH["CLIENT_ID"],
            "client_secret": settings.GLOBUS_AUTH["CLIENT_SECRET"],
        },
        # Update the local token with the new token if it is refreshed
        token_updater=lambda t: token.update(t),
    )
    try:
        response = globus_oauth.get(
            settings.GLOBUS_AUTH["LINK_URL"], verify=settings.GLOBUS_AUTH["TLS_VERIFY"]
        )
    except InvalidGrantError:
        # If the grant is invalid, redirect to globus_authorise
        # Note that the token is already removed from the session
        return redirect("globus_authorise")
    if response.status_code == 200:

        try:
            globusaccountid = json.loads(response.content)["username"]
            # Also, update the user's globus account ID in Keycloak
            keycloak_apply_globus_link(request.user, globusaccountid)

            # If the account linking was successful, store the OAuth token for later
            CEDAUser.objects.filter(username=request.user.username).update(
                globusaccountid=globusaccountid
            )
            messages.success(request, "GLOBUS account linked successfully")

        except Exception as e:
            LOG.error("Error while linking GLOBUS account to %s: %s", request.user, e)
            messages.error(request, "Error while linking GLOBUS account")
    else:
        try:
            # If we can extract an error message from an error response, then just
            # report it to the user
            messages.error(request, response.json()["error_message"])
        except Exception:
            # If we can't extract an error message from the error response, it might
            # be something more serious, so log it
            LOG.error(
                "Error while linking GLOBUS account to %s: %s %s",
                request.user,
                response.status_code,
                response.reason,
            )
            messages.error(request, "Error while linking GLOBUS account")
    return redirect("globus_account")