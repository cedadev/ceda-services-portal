__author__ = "Rhys Evans"
__date__ = "2021-02-18"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD-3-Clause"

import base64
import logging
from datetime import timedelta

from django.utils import timezone
from rest_framework import exceptions
from rest_framework.decorators import api_view
from rest_framework.response import Response as ApiResponse

from ...models import AccessTokens, CEDAUser
from .. import common

LOG = logging.getLogger(__name__)


@api_view(["POST"])
def access_token_api_create(request):
    auth = request.META.get("HTTP_AUTHORIZATION", b"")

    auth = auth.split()

    if not auth or auth[0].lower() != "basic":
        return None

    if len(auth) == 1:
        msg = "Invalid basic header. No credentials provided."
        raise exceptions.AuthenticationFailed(msg)
    elif len(auth) > 2:
        msg = "Invalid basic header. Credentials string should not contain spaces."
        raise exceptions.AuthenticationFailed(msg)

    try:
        try:
            auth_decoded = base64.b64decode(auth[1]).decode("utf-8")
        except UnicodeDecodeError:
            auth_decoded = base64.b64decode(auth[1]).decode("latin-1")
        auth_parts = auth_decoded.partition(":")
    except (TypeError, UnicodeDecodeError) as e:
        msg = "Invalid basic header. Credentials not correctly base64 encoded."
        raise exceptions.AuthenticationFailed(msg) from e
    except Exception as e:
        msg = e
        raise exceptions.AuthenticationFailed(msg) from e

    userid, password = auth_parts[0], auth_parts[2]
    user = CEDAUser.objects.filter(username=userid).first()

    response = common.create_access_token(password, userid, force=True)
    response_json = response.json()

    api_response = {}
    if response.status_code == 200:
        logging.error(response_json)
        token = AccessTokens.objects.filter(user=user).order_by("expiry")[0]
        response = common.delete_access_token(token=token)
        AccessTokens.objects.create(
            token=response_json["access_token"],
            user=CEDAUser.objects.filter(username=userid).first(),
            expiry=timezone.now() + timedelta(seconds=int(response_json["expires_in"])),
            token_name=request.POST.get("token_name", None),
        )
        api_response = {"access_token": response_json["access_token"]}
    else:
        api_response = response_json

    return ApiResponse(data=api_response, status=response.status_code)


@api_view(["POST"])
def access_token_api_delete(request):
    auth = request.META.get("HTTP_AUTHORIZATION", b"")

    auth = auth.split()

    if not auth or auth[0].lower() != "basic":
        return None

    if len(auth) == 1:
        msg = "Invalid basic header. No credentials provided."
        raise exceptions.AuthenticationFailed(msg)
    elif len(auth) > 2:
        msg = "Invalid basic header. Credentials string should not contain spaces."
        raise exceptions.AuthenticationFailed(msg)

    try:
        try:
            auth_decoded = base64.b64decode(auth[1]).decode("utf-8")
        except UnicodeDecodeError:
            auth_decoded = base64.b64decode(auth[1]).decode("latin-1")
        auth_parts = auth_decoded.partition(":")
    except (TypeError, UnicodeDecodeError) as e:
        msg = "Invalid basic header. Credentials not correctly base64 encoded."
        raise exceptions.AuthenticationFailed(msg) from e
    except Exception as e:
        msg = e
        raise exceptions.AuthenticationFailed(msg) from e

    userid, password = auth_parts[0], auth_parts[2]
    user = CEDAUser.objects.filter(username=userid)

    # if not user:
    #     msg = 'Invalid password'
    #     raise exceptions.AuthenticationFailed(msg)

    find_token = AccessTokens.objects.filter(
        user=user[0], token=request.POST.get("token")
    )

    if len(find_token) < 1:
        raise exceptions.NotFound("Could not find token")

    response = common.delete_access_token(token_name=request.POST.get("token"))

    if response.status_code == 200:
        api_response = {"deleted": True, "access_token": find_token[0].token}
    else:
        api_response = {"status_code": response.status_code, "json": response.json()}

    return ApiResponse(data=api_response, response=response.status_code)
