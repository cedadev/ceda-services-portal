""" Utility functions for the accounts app. """

__author__ = "William Tucker"
__date__ = "2023-12-11"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"


import django
import keycloak
import logging

logger = logging.getLogger(__name__)


def keycloak_apply_jasmin_link(user, jasminaccountid):
    """Add a JASMIN account ID to a user as a Keycloak attribute."""

    settings = django.conf.settings.JASMIN_SERVICES["KEYCLOAK"]

    keycloak_admin = keycloak.KeycloakAdmin(
        server_url=settings.get("SERVER_URL"),
        realm_name=settings.get("REALM_NAME"),
        username=settings.get("USERNAME"),
        password=settings.get("PASSWORD"),
        user_realm_name=settings.get("USER_REALM_NAME", settings.get("REALM_NAME")),
        verify=settings.get("VERIFY", True),
    )

    logger.info(
        f"Applying keycloak attribute {jasminaccountid} to user {user.username}."
    )
    kc_user_id = keycloak_admin.get_user_id(user.username)
    attributes = keycloak_admin.get_user(kc_user_id).get("attributes", {})
    attributes.update({"jasminaccountid": jasminaccountid})

    keycloak_admin.update_user(kc_user_id, {"attributes": attributes})
