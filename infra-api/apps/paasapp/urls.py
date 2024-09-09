from django.urls import path

from .v1 import views
from .v2 import views as views_v2

urlpatterns = [
    path("v1/create_access", views.ApiPaasView.as_view(), name="create_access"),
    path("v2/create_access", views_v2.ApiPaasViewV2.as_view(), name="create_access"),
    path("v1/groups", views.LDAPGroups.as_view(), name="groups"),
    path("v1/ports", views.UTMService.as_view(), name="services"),
    path("v1/interfaces", views.UTMInterface.as_view(), name="interfaces"),
    path("v1/sync", views_v2.UTMPoliciesView.as_view(), name="sync"),
]
