'''
Created on Oct 11, 2017

@author: William Tucker
'''

import logging

from django.conf import settings
from django.contrib.auth import logout, login, get_user_model


logger = logging.getLogger(__name__)


class LoginMiddleware():
    """
    Middleware that checks for a valid login in the request
    and logs the user in
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        User = get_user_model()

        # Check if the user has been authenticated externally
        userid = None
        if hasattr(request, 'authenticated_user'):
            userid = request.authenticated_user.get('userid')

        if request.user.is_authenticated:
            
            # Logout user if session is not valid
            if not userid:

                custom_auth = getattr(settings, 'DJ_SECURITY_AUTH_CHECK', None)
                if custom_auth and not custom_auth(request):
                    logout(request)

            elif userid != request.user.username:
                logout(request)

        elif userid:
            
            # Create user with userid if they don't exist yet
            if not User.objects.filter(username=userid).exists():
                user = User.objects.create_user(username=userid,
                                                password=None)

            # Prepare session for user
            user = User.objects.get(username=userid)

            if not request.user.is_authenticated:
                user = User.objects.filter(username=userid).first()
                login(request, user)

        response = self.get_response(request)
        return response
