import django.conf
import django.core.exceptions
import httpx
import jasmin_services.views
from django.core.cache import cache


class CEDARoleApplyView(jasmin_services.views.RoleApplyView):
    """Subclass RoleApplyView to add CEDA specific logic.

    This is mostly licence handling.
    """

    def __init__(self, *args, **kwargs):
        self.licence_url = django.conf.settings.CEDA_SERVICES["LICENCE_URL"]
        self.httpx_client = httpx.Client()
        super().__init__(*args, **kwargs)

    def get_licence_info(self, service_name):
        """Get the licence info from the access instructor."""
        cache_key = f"cedaservices-licence-{service_name}"
        licence_info = cache.get(cache_key)
        if licence_info is None:
            licence_info = self.httpx_client.get(
                self.licence_url, params={"group": service_name}
            ).json()
        if "error" in licence_info.keys():
            raise django.core.exceptions.ObjectDoesNotExist(str(licence_info["error"]))
        return licence_info

    def get_context_data(self, **kwargs):
        """Add licence url into the request data."""
        context = super().get_context_data(**kwargs)
        context["licence_url"] = self.get_licence_info(self.service.name)
        return context
