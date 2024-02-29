import logging

import django.conf
import django.contrib.messages
import django.core.exceptions
import django.forms.widgets
import httpx
import jasmin_services.views
from django.core.cache import cache

logger = logging.getLogger()


class CEDARoleApplyView(jasmin_services.views.RoleApplyView):
    """Subclass RoleApplyView to add CEDA specific logic.

    This is mostly licence handling.
    """

    def __init__(self, *args, **kwargs):
        self.licence_url = django.conf.settings.CEDA_SERVICES["LICENCE_URL"]
        self.httpx_client = httpx.Client()
        super().__init__(*args, **kwargs)

    def setup(self, request, *args, **kwargs):
        """Add licence info for use in form and context."""
        # pylint: disable=attribute-defined-outside-init
        super().setup(request, *args, **kwargs)
        try:
            self.licence_info = self.get_licence_info(self.service.name)
        except django.core.exceptions.ObjectDoesNotExist:
            self.licence_info = None

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to provide a nice error message if a service has no licence."""
        if self.licence_info is None:
            django.contrib.messages.error(
                request,
                f"You cannot apply for {self.service.name}, because no licence was found. Please contact support for assistance.",
            )
            return jasmin_services.views.common.redirect_to_service(self.service)
        return super().dispatch(request, *args, **kwargs)

    def get_licence_info(self, service_name):
        """Get the licence info from the access instructor."""
        # Get the licence from the cache if available.
        cache_key = f"cedaservices-licence-{service_name}"
        licence_info = cache.get(cache_key)
        # Otherwise get it from the access instructor.
        if licence_info is None:
            licence_info = self.httpx_client.get(
                self.licence_url, params={"group": service_name}
            ).json()
        # Annoyingly if there is an error the API returns 200 with a dict with a single key "error"
        # Otherwise, it returns a list of dicts of licences.
        if isinstance(licence_info, dict) and "error" in licence_info.keys():
            logger.error("Licence for group %s does not exist.", service_name)
            raise django.core.exceptions.ObjectDoesNotExist(str(licence_info["error"]))
        # Exactly one licence should be returned.
        # We don't handle the case where more than one is returned.
        if len(licence_info) > 1:
            raise django.core.exceptions.MultipleObjectsReturned()
        # Cache the licence response for 10 minutes.
        cache.set(cache_key, licence_info, 600)
        return licence_info[0]

    def get_context_data(self, **kwargs):
        """Add licence url into the request data."""
        context = super().get_context_data(**kwargs)
        context["licence_url"] = self.licence_info["url_link"]
        return context

    def get_initial(self):
        """Inject the licence_url into the initial form data."""
        initial = super().get_initial()
        initial["licence_url"] = self.licence_info["url_link"]
        return initial

    def get_form(self, form_class=None):
        """Override the licence_url field to hide it from the users."""
        form = super().get_form(form_class)
        form.fields["licence_url"].widget = django.forms.widgets.HiddenInput()
        return form

    def form_valid(self, form):
        """Confirm that the licence URL sent has not been changed by the user.

        By doing it this way, we also ensure that the URL the user was shown is always the same
        as the one stored in the database.
        """
        if form.cleaned_data["licence_url"] != self.licence_info["url_link"]:
            raise django.core.exceptions.SuspiciousOperation()
        return super().form_valid(form)
