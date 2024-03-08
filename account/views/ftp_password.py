__author__ = "Rhys Evans"
__date__ = "2021-02-18"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD-3-Clause"

import base64
import logging
import random
import string

from crypto_cookie.encoding import Encoder
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from ..models import CEDAUser
from ..rabbit import RabbitConnection

LOG = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
@login_required
def account_ftp_password(request):
    """
    Handle ``/account/ftp/``.

    Responds to GET requests only.

    Allows the user to create or reset their ftp password.
    """
    # Create new ftp password.
    if request.method == "POST":
        CEDAUser.objects.filter(username=request.user.username).update(
            has_ftp_password=True
        )
        password = "".join(
            random.choices(
                string.ascii_letters + string.digits + string.punctuation, k=12
            )
        )
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

    return render(request, "account/ftp_password.html", {"password": password})
