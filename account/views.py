from rest_framework.response import Response
from rest_framework.decorators import api_view
from jasmin_services.models import Category, Service

@api_view(['GET'])
def create_service(request):
    category_name = request.GET.get('category_name')
    category_long_name = request.GET.get('category_long_name')
    category, _ = Category.objects.get_or_create(
        name=category_name,
        long_name=category_long_name,
    )

    service_name = request.GET.get('service_name')
    service_summary = request.GET.get('service_summary')
    service = Service(
        category=category,
        name=service_name,
        summary=service_summary,
    )
    service.save()

    return Response({"message": "Serivce " + service_name + " created"})
