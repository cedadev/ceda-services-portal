"""
This module provides a Django models that can be used for querying and
manipulating CEDA user accounts.
"""

__author__ = "William Tucker"
__date__ = "2019-08-28"
__copyright__ = "Copyright 2019 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level directory"


from datetime import date
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import models
from django.contrib.auth import models as auth_models
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField
from django_countries.fields import CountryField
from jasmin_notifications.models import NotifiableUserMixin


class Institution(models.Model):
    """
    Model class representing an institution that a user can belong to.
    """
    class Meta:
        ordering = ('name', 'country')

    #: The name of the institution
    name = models.CharField(max_length=200)
    #: The country of the institution
    country = CountryField()
    #: The type of the institution
    institution_type = models.CharField(
        max_length=20,
        choices=[
            ("NERC", "NERC"),
            ("University", "University"),
            ("School", "School"),
            ("Government", "Government"),
            ("Commercial", "Commercial"),
            ("Other", "Other"),
        ]
    )

    def __str__(self):
        return "{}, {}".format(self.name, self.country.name)


class CEDAUser(auth_models.AbstractUser, NotifiableUserMixin):
    """
    Custom user model for the `ceda_auth` package.
      * Provides access to the :py:class:`Account` for the user as a cached property
      * Adds additional fields for 'suspension reason'
      * Tracks email confirmation
    """
    class Meta:
        verbose_name = 'CEDA User'
        verbose_name_plural = 'CEDA Users'
        ordering = ('username', )

    # This is mostly for createsuperuser
    REQUIRED_FIELDS = ['email', 'first_name',
                       'last_name', 'discipline', 'institution_id']

    # Modify these fields to be required
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    #: The discipline that the user studies
    DISCIPLINE_CHOICES = [
        ("Atmospheric Physics", "Atmospheric Physics"),
        ("Atmospheric Chemistry", "Atmospheric Chemistry"),
        ("Climate Change", "Climate Change"),
        ("Earth System Science", "Earth System Science"),
        ("Marine Science", "Marine Science"),
        ("Terrestrial and Fresh Water", "Terrestrial and Fresh Water"),
        ("Earth Observation", "Earth Observation"),
        ("Polar Science", "Polar Science"),
        ("Geography", "Geography"),
        ("Engineering", "Engineering"),
        ("Medical/Biological Sciences", "Medical/Biological Sciences"),
        ("Mathematics/Computer Science", "Mathematics/Computer Science"),
        ("Economics", "Economics"),
        ("Personal use", "Personal use"),
        ("Other", "Other"),
    ]
    discipline = models.CharField(
        max_length=30,
        choices=DISCIPLINE_CHOICES,
        help_text='Please select the closest match to the discipline that you work in'
    )
    #: The type of degree that the user is studying for
    DEGREE_CHOICES = [
        ("", "Not studying for a degree"),
        ("First degree", "First Degree (Bachelor's / Undergraduate Master's)"),
        ("Postgraduate Master's", "Postgraduate Master's"),
        ("Doctorate", "Doctorate"),
        ("Other", "Other"),
    ]
    degree = models.CharField(
        max_length=30, blank=True,
        choices=DEGREE_CHOICES,
        help_text='The type of degree you are studying for, if applicable'
    )
    #: The user's institution
    institution = models.ForeignKey(
        Institution, models.CASCADE, null=True,  blank=True)

    #: Indicates if the user is a service user
    service_user = models.BooleanField(
        default=False,
        help_text='Indicates if this user is a service user, i.e. a user that '
        'exists to run a service rather than a regular user account.'
    )
    #: If this is a service user, these are the responsible users
    responsible_users = models.ManyToManyField(
        "self",
        symmetrical=False, blank=True,
        limit_choices_to={'service_user': False},
        help_text='For service users, these are the users responsible for the '
        'administration of the service user.'
    )

    #: The time at which the user last confirmed their email address
    email_confirmed_at = models.DateTimeField(null=True, blank=True)

    #: The time at which the user accepted the JASMIN Terms and Conditions
    conditions_accepted_at = models.DateTimeField(null=True, blank=True)

    #: The username of the user who approved this user for root access
    approved_for_root_by = models.CharField(
        max_length=200, null=True, blank=True)
    #: The datetime at which the user was approved for root access
    approved_for_root_at = models.DateTimeField(null=True, blank=True)

    #: The reason why the user was suspended (for the user)
    user_reason = models.TextField(
        blank=True,
        verbose_name='Reason for suspension (user)',
        help_text='Indicate why the user has been suspended'
    )
    #: Internal details on user suspension
    internal_reason = models.TextField(
        blank=True,
        verbose_name='Reason for suspension (internal)',
        help_text='Any internal details about the user\'s suspension that '
        'should not be displayed to the user'
    )

    def email_confirm_required(self):
        """
        Returns true if the user needs to confirm their email address soon, false
        otherwise.
        """
        if not self.email_confirmed_at:
            return False
        deltas = settings.CEDA_AUTH['EMAIL_CONFIRM_NOTIFY_DELTAS']
        confirm_by = self.email_confirmed_at.date() + relativedelta(years=1)
        threshold = date.today() + deltas[0]
        return confirm_by < threshold

    def clean(self):
        errors = {}
        # Ensure that an account with the current username exists
        # if not Account.objects.filter(username = self.username).exists():
        #     errors['username'] = 'An account with this username does not exist.'
        if self.email:
            # If email is given, it must be case-insensitive unique
            q = CEDAUser.objects.filter(email__iexact=self.email)
            if not self._state.adding:
                q = q.exclude(pk=self.pk)
            if q.exists():
                errors['email'] = 'Email address is already in use.'
        elif not self.service_user:
            # Email address is required for regular users
            errors['email'] = 'This field is required.'
        # Ensure that a reason is given if the account is suspended
        if self.is_active:
            if self.user_reason:
                errors['user_reason'] = 'Must not be present for active account.'
            if self.internal_reason:
                errors['internal_reason'] = 'Must not be present for active account.'
        else:
            if not self.user_reason:
                errors['user_reason'] = 'Please give a reason for suspension.'
        if self.approved_for_root_by and not self.approved_for_root_at:
            errors['approved_for_root_at'] = 'Required to indicate root access is approved.'
        if self.approved_for_root_at and not self.approved_for_root_by:
            errors['approved_for_root_by'] = 'Required to indicate root access is approved.'
        if errors:
            raise ValidationError(errors)

    def check_password(self, raw_password):
        # For service users, the password is *never* correct
        if self.service_user:
            return False
        # The "canonical" password is the one for the LDAP account
        if not super().check_password(raw_password):
            self.set_password(raw_password)
            # Don't treat this is a password reset
            self._password = None
            self.save(update_fields=['password'])
            return True
        else:
            return False

    def set_password(self, raw_password):
        # For service users, always set an unusable password
        if self.service_user:
            self.set_unusable_password()
            return
        super().set_password(raw_password)

    def notify(self, *args, **kwargs):
        # During an import, disable all notifications
        if getattr(settings, 'IS_CEDA_IMPORT', False):
            return
        # Only send notifications for migrated users
        # If there is no MIGRATED_USERS setting, then assume all users are migrated
        if self.username not in getattr(settings, 'MIGRATED_USERS', [self.username]):
            return
        # For service users, we want to notify the responsible users instead
        if self.service_user:
            for user in self.responsible_users.all():
                user.notify(*args, **kwargs)
        else:
            super().notify(*args, **kwargs)

    def notify_if_not_exists(self, *args, **kwargs):
        # During an import, disable all notifications
        if getattr(settings, 'IS_CEDA_IMPORT', False):
            return
        # Only send notifications for migrated users
        # If there is no MIGRATED_USERS setting, then assume all users are migrated
        if self.username not in getattr(settings, 'MIGRATED_USERS', [self.username]):
            return
        # For service users, we want to notify the responsible users instead
        if self.service_user:
            for user in self.responsible_users.all():
                user.notify_if_not_exists(*args, **kwargs)
        else:
            super().notify_if_not_exists(*args, **kwargs)

    def notify_pending_deadline(self, *args, **kwargs):
        # During an import, disable all notifications
        if getattr(settings, 'IS_CEDA_IMPORT', False):
            return
        # Only send notifications for migrated users
        # If there is no MIGRATED_USERS setting, then assume all users are migrated
        if self.username not in getattr(settings, 'MIGRATED_USERS', [self.username]):
            return
        # For service users, we want to notify the responsible users instead
        if self.service_user:
            for user in self.responsible_users.all():
                user.notify_pending_deadline(*args, **kwargs)
        else:
            super().notify_pending_deadline(*args, **kwargs)


class OAuthToken(models.Model):
    """
    Model representing an OAuth token from the CEDA OAuth server for a user. A
    user may have at most one token at any one time.
    """
    class Meta:
        verbose_name = 'OAuth Token'

    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                models.CASCADE, related_name='oauth_token')
    token_type = models.CharField(max_length=20)
    # NOTE: ArrayField is **Postgres specific**
    scope = ArrayField(models.CharField(max_length=250))
    access_token = models.CharField(max_length=50)
    refresh_token = models.CharField(max_length=50)
    expires_at = models.FloatField()
    expires_in = models.IntegerField()

    def as_dict(self):
        """
        Returns a token dict representing the token for use with `requests-oauthlib`.
        """
        return {
            'token_type': self.token_type,
            'scope': self.scope,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_at': self.expires_at,
            'expires_in': self.expires_in,
        }
