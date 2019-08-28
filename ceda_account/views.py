""" Views for the ceda_account app. """

__author__ = "William Tucker"
__date__ = "2019-08-28"
__copyright__ = "Copyright 2019 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level directory"


from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView


@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    template_name = 'ceda_account/profile.html'
