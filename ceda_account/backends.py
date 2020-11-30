""" Module for the authentication backend. """

__author__ = "William Tucker"
__date__ = "2020-09-21"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"


from oidc_auth.backends import OIDCAuthenticationBackend

from ceda_account.models import Institution


class CEDAAuthenticationBackend(OIDCAuthenticationBackend):

    def get_username(self, claims):

        return claims.get("preferred_username")

    def create_user(self, claims):

        email = claims.get('email')
        username = self.get_username(claims)

        first_name = claims.get("given_name", "")
        last_name = claims.get("family_name", "")
        discipline = claims.get("discipline", "")

        institution = Institution.objects.get(id=0)
        institution_name = claims.get("institution", None)
        if institution_name:
            institution = Institution.objects.get(name=institution_name)

        return self.UserModel.objects.create_user(username, email, first_name=first_name, last_name=last_name, discipline=discipline, institution_id=institution.id)

    def update_user(self, user, claims):

        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.save()

        return user
