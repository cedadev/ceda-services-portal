""" Module for the authentication backend. """

__author__ = "William Tucker"
__date__ = "2020-09-21"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"


import logging

from oidc_auth.backends import OIDCAuthenticationBackend

from account.models import Institution


log = logging.getLogger(__name__)


class CEDAAuthenticationBackend(OIDCAuthenticationBackend):

    @staticmethod
    def _parse_user_attributes(claims):

        institution = None
        institution_name = claims.get("institute", "")
        institution, created = Institution.objects.get_or_create(
            name=institution_name,
            institution_type=claims.get("institute_type", "Other")
        )

        institution_country = claims.get("institute_country", "")
        if len(institution_country) == 2:
            institution.country = institution_country
            institution.save()

        return {
            "first_name": claims.get("given_name"),
            "last_name": claims.get("family_name"),
            "discipline": claims.get("discipline", "Other"),
            "institution_id": institution.id
        }

    def get_username(self, claims):

        return claims.get("preferred_username")

    def create_user(self, claims):

        email = claims.get('email')
        username = self.get_username(claims)

        attributes = self._parse_user_attributes(claims)
        return self.UserModel.objects.create_user(username, email, **attributes)

    def update_user(self, user, claims):

        attributes = self._parse_user_attributes(claims)
        for attribute, value in attributes.items():
            setattr(user, attribute, value)
        user.save()

        return user
