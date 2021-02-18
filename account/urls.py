from django.urls import path, include
from . import views


urlpatterns = [
    path('service/create/', views.create_service),
]