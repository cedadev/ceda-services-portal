"""
Registration of the auth models with the default admin interface.
"""

__author__ = "Matt Pryor"
__copyright__ = "Copyright 2015 UK Science and Technology Facilities Council"

from datetime import datetime, date

from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.db.models import Count
from django.conf.urls import url
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied
from django.contrib.admin.options import IS_POPUP_VAR
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib import messages

from django_countries import countries

from .models import (
    CEDAUser,
    OAuthToken,
    Institution,
)
from .forms import (
    CEDAUserCreateForm,
    CEDAUserChangeForm,
)
from .actions import send_confirmation_notifications, suspend_unresponsive_users

class _InstituteCountryIfAnyFilter(admin.SimpleListFilter):
    """
    Filter for the country of an institution that only displays countries with
    some results.
    """
    title = 'country'
    parameter_name = 'country'

    def lookups(self, request, model_admin):
        # Get the list of unique country codes where there is an institution
        qs = model_admin.get_queryset(request)
        codes = qs.order_by('country').values_list('country', flat = True).distinct()
        return [(code, countries.name(code)) for code in codes]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(country = self.value())

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'institution_type', 'n_users')
    list_filter = ('institution_type', _InstituteCountryIfAnyFilter)
    search_fields = ('name', )

    def n_users(self, obj):
        return obj.jasminuser_set.count()
    n_users.short_description = '# users'


class OAuthTokenInline(admin.TabularInline):
    model = OAuthToken
    readonly_fields = ('token_type', 'scope', 'access_token',
                       'refresh_token', 'expires_at', 'expires_in')

@admin.register(CEDAUser)
class CEDAUserAdmin(auth_admin.UserAdmin):
    inlines = [OAuthTokenInline]
    actions = ['send_confirmation_notifications', 'suspend_unresponsive_users']
    list_display = ('username', 'email', 'first_name', 'last_name', 'institution',
                    'service_user', 'is_active', 'is_staff')
    list_filter = auth_admin.UserAdmin.list_filter  \
                + ('service_user', 'discipline', 'degree',
                   'institution', 'institution__institution_type')
    search_fields = auth_admin.UserAdmin.search_fields + ('institution__name', )

    add_form = CEDAUserCreateForm
    form = CEDAUserChangeForm
    add_form_template = 'admin/jasmin_auth/jasminuser/add_form.html'
    add_fieldsets = (
        (None, { 'fields' : ('username', 'password1', 'password2') }),
        ('Account Details', {
            'fields' : ('first_name', 'last_name', 'email',
                        'service_user', 'responsible_users',
                        'discipline', 'degree', 'institution'),
        }),
    )
    fieldsets = (
        (None, { 'fields' : ('username', 'password') }),
        ('Account Details', {
            'fields' : ('first_name', 'last_name', 'email',
                        'service_user', 'responsible_users',
                        'discipline', 'degree', 'institution'),
        }),
        ('CEDA Permissions', {
            'fields' : ('otp_required', 'is_active', 'user_reason', 'internal_reason',
                        'approved_for_root_by', 'approved_for_root_at'),
            'classes' : ('collapse', ),
        }),
        ('Django Permissions', {
            'fields' : ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes' : ('collapse', ),
        }),
        ('Important dates', {
            'fields' : ('email_confirmed_at', 'conditions_accepted_at',
                        'last_login', 'date_joined'),
            'classes' : ('collapse', ),
        }),
    )
    filter_horizontal = auth_admin.UserAdmin.filter_horizontal + ('responsible_users', )

    def get_readonly_fields(self, request, obj = None):
        # Once created, username is readonly
        if getattr(obj, 'pk', None):
            return tuple(self.readonly_fields or ()) + ('username', )
        else:
            return self.readonly_fields

    def get_inline_instances(self, request, obj = None):
        # When creating, don't show the inlines
        if not getattr(obj, 'pk', None):
            return []
        return super().get_inline_instances(request, obj)

    def send_confirmation_notifications(self, request, queryset):
        """
        Admin action that processes confirmation requests to ensure users confirm
        their email address periodically, or their account is suspended.
        """
        send_confirmation_notifications(queryset)
    send_confirmation_notifications.short_description = 'Send confirmation notifications'

    def suspend_unresponsive_users(self, request, queryset):
        """
        Admin action that processes confirmation requests to ensure users confirm
        their email address periodically, or their account is suspended.
        """
        suspend_unresponsive_users(queryset)
    suspend_unresponsive_users.short_description = 'Suspend unresponsive users'
