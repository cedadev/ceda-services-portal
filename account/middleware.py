import django.contrib.messages

from . import exceptions


class ExceptionHandlingMiddleware:
    """Handle uncaught exceptions instead of raising a 500 error."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, exceptions.LicenceNotFoundError):
            django.contrib.messages.error(
                request,
                "The dataset you applied for has no licences available. Please contact support@ceda.ac.uk for more information.",
            )
        return None
