"""
This module provides forms for editing the models provided by the CEDA auth app.
"""

__author__ = "William Tucker"
__date__ = "2019-08-28"
__copyright__ = "Copyright 2019 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level directory"


from django import forms
from django.contrib.auth import forms as auth_forms
from django.core.exceptions import ValidationError

from .models import CEDAUser


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CEDAUser
        fields = ('first_name', 'last_name', 'discipline', 'degree')


########
# Admin forms
########


class CEDAUserFormMixin:
    def clean_responsible_users(self):
        service_user = self.cleaned_data.get('service_user', False)
        responsible_users = self.cleaned_data.get('responsible_users')
        if service_user and not responsible_users:
            raise ValidationError('This field is required.')
        return responsible_users


class CEDAUserCreateForm(auth_forms.UserCreationForm, CEDAUserFormMixin):
    """
    Customised user form for creating CEDA users.
    """
    class Meta:
        model = CEDAUser
        fields = ('username', 'first_name', 'last_name',
                  'email', 'service_user', 'responsible_users')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = 'Not required for service users.'
        self.fields['password1'].required = False
        self.fields['password2'].required = False

    def clean_password2(self):
        # Only run the password2 validations if password1 is present
        password1 = self.cleaned_data.get('password1')
        if password1:
            return super().clean_password2()
        else:
            return self.cleaned_data.get('password2')

    def clean(self):
        cleaned_data = super().clean()
        service_user = cleaned_data.get('service_user', False)
        password1 = cleaned_data.get('password1')
        if not service_user and not password1:
            raise ValidationError({
                'password1': 'This field is required.'
            })
        return cleaned_data


class CEDAUserChangeForm(auth_forms.UserChangeForm, CEDAUserFormMixin):
    """
    Customised user form for changing CEDA users.
    """
