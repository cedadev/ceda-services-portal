""" Django app views module """

__author__ = "Rhys Evans"
__date__ = "2021-02-18"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"


from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.views import APIView
from rest_framework.response import Response
from jasmin_services.models import Category, Service, Role, RoleObjectPermission, Request
from jasmin_metadata.models import Form


class ServiceCreate(APIView):
    """
    List all snippets, or create a new snippet.
    """

    def get(self, request, *args, **kwargs):

        category = Category.objects.get(name=request.data["category"])

        name = request.data.get('name')
        summary = request.data.get('summary')
        hidden = request.data.get('hidden')
        service, created = Service.objects.get_or_create(
            category=category,
            name=name
        )
        if created:
            service.summary = summary
            service.hidden = hidden

            self.save_related(service)

            service.save()

        return Response({"message": f"Service {name} created"})

    def get_role_permissions(self):
        return (
            Permission.objects.get(
                content_type = ContentType.objects.get_for_model(Role),
                codename = 'view_users_role',
            ),
            Permission.objects.get(
                content_type = ContentType.objects.get_for_model(Role),
                codename = 'send_message_role',
            ),
            Permission.objects.get(
                content_type = ContentType.objects.get_for_model(Request),
                codename = 'decide_request',
            ),
        )

    def create_role_object_permissions(self, role, target_role):
        permissions = self.get_role_permissions()
        RoleObjectPermission.objects.bulk_create([
            RoleObjectPermission(
                role = role,
                permission =  permission,
                content_type = ContentType.objects.get_for_model(target_role),
                object_pk = target_role.pk
            )
            for permission in permissions
        ])

    def save_related(self, service):
        default_form = Form.objects.get(pk = settings.JASMIN_SERVICES['DEFAULT_METADATA_FORM'])
        # Create the three default roles
        user_role, _ = service.roles.get_or_create(
            name = 'USER',
            defaults = dict(
                description = 'Standard user role',
                hidden = False,
                position = 100,
                metadata_form = default_form
            )
        )
        deputy_role, _ = service.roles.get_or_create(
            name = 'DEPUTY',
            defaults = dict(
                description = 'Service deputy manager role',
                hidden = True,
                position = 200,
                metadata_form = default_form
            )
        )
        self.create_role_object_permissions(deputy_role, user_role)
        manager_role, _ = service.roles.get_or_create(
            name = 'MANAGER',
            defaults = dict(
                description = 'Service manager role',
                hidden = True,
                position = 300,
                metadata_form = default_form
            )
        )
        self.create_role_object_permissions(manager_role, user_role)
        self.create_role_object_permissions(manager_role, deputy_role)

"""
@api_view(['GET'])
def create_service(request):
    category = request.GET.get('category')
    category, _ = Category.objects.get_or_create(name=category)

    name = request.GET.get('name')
    summary = request.GET.get('summary')
    hidden = request.GET.get('hidden')
    service, created = Service.objects.get_or_create(
        category=category,
        name=name
    )
    if created:
        service.summary = summary
        service.hidden = hidden
        service.save()

    return Response({"message": f"Service {name} created"})
"""
