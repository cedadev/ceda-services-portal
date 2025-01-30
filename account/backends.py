""" Module for the authentication backend. """

__author__ = "William Tucker"
__date__ = "2020-09-21"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"


import logging

from oidc_auth.backends import UsernameOIDCAuthenticationBackend

from account.models import Institution


log = logging.getLogger(__name__)


class CEDAAuthenticationBackend(UsernameOIDCAuthenticationBackend):

    @staticmethod
    def _parse_user_attributes(claims):

        institution = None
        institution_name = claims.get("institute", "None")
        institution, created = Institution.objects.get_or_create(
            name=institution_name,
            institution_type=claims.get("institute_type", "Other")
        )

        institution_country = claims.get("institute_country", "")
        if len(institution_country) == 2:
            institution.country = institution_country
            institution.save()

        return {
            "discipline": claims.get("discipline", "Other"),
            "institution_id": institution.id
        }

    def create_user(self, claims):

        username = self.get_username(claims)
        attributes = self._parse_user_attributes(claims)

        user = self.UserModel.objects.create_user(username, **attributes)
        return self.update_user(user, claims)

    def update_user(self, user, claims):

        user = super().update_user(user, claims)

        attributes = self._parse_user_attributes(claims)
        for attribute, value in attributes.items():
            setattr(user, attribute, value)
        user.save()

        return user
