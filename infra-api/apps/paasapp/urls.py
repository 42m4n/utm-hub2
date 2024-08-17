from django.urls import path

from . import views

urlpatterns = [
    path("create_access", views.ApiPaasView.as_view(), name="create_access"),
    path("groups", views.LDAPGroups.as_view(), name="groups"),
    path("ports", views.UTMService.as_view(), name="services"),
    path("interfaces", views.UTMInterface.as_view(), name="interfaces"),
]
