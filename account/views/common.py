__author__ = "Rhys Evans"
__date__ = "2021-02-18"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD-3-Clause"

import logging
import re

import requests
from django.conf import settings
from requests.models import Response
from rest_framework import exceptions

from ..models import AccessTokens, CEDAUser

LOG = logging.getLogger(__name__)


def delete_access_token(key=None, token_name=None):
    if key is not None:
        token = AccessTokens.objects.get(pk=key)
    elif token_name is not None:
        token = AccessTokens.objects.get(token=token_name)
    else:
        raise exceptions.APIException(
            {"error": "Did not provide token details"}, code=400
        )

    url = re.sub("token$", "revoke", settings.OIDC_OP_TOKEN_ENDPOINT)
    payload = f"client_id={settings.OIDC_RP_CLIENT_ID}&client_secret={settings.OIDC_RP_CLIENT_SECRET}&token={token.token}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.request(
        "POST",
        url,
        headers=headers,
        data=payload,
        verify=settings.OIDC_VERIFY_SSL,
        timeout=10,
    )

    if response.status_code == 200:
        token.delete()

    return response


def create_access_token(password, username):
    user = CEDAUser.objects.filter(username=username).first()
    # Disable filtering by expiry for now, short expiry time makes testing annoying
    # no_of_tokens = AccessTokens.objects.filter(user=user, expiry__gte=datetime.now())
    no_of_tokens = AccessTokens.objects.filter(user=user)

    if len(no_of_tokens) >= 2:
        response = Response()
        response.code = "forbidden"
        response.error_type = "forbidden"
        response.status_code = 403
        response._content = (
            b'{"error_description" : "You may only have 2 access tokens" }'
        )
        return response

    url = settings.OIDC_OP_TOKEN_ENDPOINT
    payload = f"username={ username }&password={ password }&client_id={settings.OIDC_RP_CLIENT_ID}&client_secret={settings.OIDC_RP_CLIENT_SECRET}&grant_type=password"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.request(
        "POST",
        url,
        headers=headers,
        data=payload,
        verify=settings.OIDC_VERIFY_SSL,
        timeout=10,
    )
    return response


def _get_rabbit_producer_class():
    if hasattr(settings, "RABBIT_SERVER") and "PRODUCER" in settings.RABBIT_SERVER:
        module_path, _, class_name = settings.RABBIT_SERVER["PRODUCER"].rpartition(".")
        connector_module = __import__(module_path, fromlist=[class_name])
    else:
        return RabbitProducer
    return getattr(connector_module, class_name)
