"""
Actions for the auth app that can be run via the admin or as management
commands.
"""

__author__ = "William Tucker"
__date__ = "2019-08-28"
__copyright__ = "Copyright 2019 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level directory"


from datetime import date
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.urls import reverse


def send_confirmation_notifications(queryset):
    """
    Send warning notifications for users in the given queryset when the deadline
    for confirmation of their email address is approaching.
    """
    deltas = settings.EMAIL_CONFIRM_NOTIFY_DELTAS
    # Send notifications for users who are within the biggest delta of requiring
    # an email confirmation
    deadline = date.today() - relativedelta(years=1) + deltas[0]
    for user in queryset.exclude(email__isnull=True)  \
                        .exclude(email='')  \
                        .filter(is_active=True,
                                service_user=False,
                                email_confirmed_at__date__lte=deadline):
        user.notify_pending_deadline(
            user.email_confirmed_at.date() + relativedelta(years=1),
            deltas,
            'account_email_confirm_required',
            user,
            reverse('jasmin_auth:profile')
        )


def suspend_unresponsive_users(queryset):
    """
    Suspends any users in the given queryset that have not confirmed their email
    for over a year.
    """
    # Find all the active users who confirmed their email address more than a year
    # ago and suspend them
    one_year_ago = date.today() - relativedelta(years=1)
    for user in queryset.exclude(email__isnull=True)  \
                        .exclude(email='')  \
                        .filter(is_active=True,
                                service_user=False,
                                email_confirmed_at__date__lt=one_year_ago):
        user.is_active = False
        user.user_reason = 'Failed to respond to email confirmation request.'
        user.save()
