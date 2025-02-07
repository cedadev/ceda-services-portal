"""Module providing a custom admin site."""

import collections
import inspect
import typing

import django.contrib.auth
import django.urls
import django.utils.http
import django.views
from django.contrib import admin
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render
from django.urls import URLPattern, URLResolver, path
from django.utils.translation import gettext as _

_FuncT = typing.NewType("_FuncT", typing.Callable[..., typing.Any])

AdminView = collections.namedtuple(
    "AdminView", ["path", "view", "name", "urlname", "visible"]
)


def is_class_based_view(view):
    return inspect.isclass(view) and issubclass(view, django.views.View)


class AdminSite(admin.AdminSite):
    """
    Admit site which allows loading extra views.

    It also uses the standard site login view rather than a separate login view.
    """

    def __init__(self, *args, **kwargs) -> None:
        self.custom_views: list[AdminView] = []
        super().__init__(*args, **kwargs)

    def login(self, request, extra_context=None):
        """Use the main site login instead of admin one."""
        next_url = request.GET.get(django.contrib.auth.REDIRECT_FIELD_NAME)
        if not next_url or not django.utils.http.url_has_allowed_host_and_scheme(
            url=next_url, allowed_hosts={request.get_host()}
        ):
            next_url = django.urls.reverse("admin:index", current_app=self.name)
        if request.user.is_authenticated:
            # If the user is already authenticated but doesn't have permission, show a template
            if not self.has_permission(request):
                return render(
                    request,
                    "admin/permission_denied.html",
                    dict(
                        self.each_context(request),
                        title=_("Log in"),
                    ),
                )
        # Otherwise, redirect the user to log in
        return redirect_to_login(next_url)

    def register_view(
        self, slug, name=None, urlname=None, visible=True, view=None
    ) -> typing.Union[None, typing.Callable[[_FuncT], _FuncT]]:
        """Add a custom admin view. Can be used as a function or a decorator.

        slug is the path in the admin where the view will be
        name is an optional name for the list of custom views
        urlname is an optional parameter to be able to redirect() or reverse()
        visible controls is the view shows in the dashboard
        view is any view function or class.
        """

        def decorator(fn: _FuncT):
            if is_class_based_view(fn):
                fn = fn.as_view()
            self.custom_views.append(AdminView(slug, fn, name, urlname, visible))
            return fn

        if view is not None:
            decorator(view)
            return
        return decorator

    def get_urls(self) -> typing.Sequence[typing.Union[URLPattern, URLResolver]]:
        """Add our custom views to the admin urlconf."""
        urls: list[typing.Union[URLPattern, URLResolver]] = super().get_urls()

        for view in self.custom_views:
            urls.insert(
                0, path(view.path, self.admin_view(view.view), name=view.urlname)
            )
        return urls
