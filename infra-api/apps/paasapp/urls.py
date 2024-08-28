from django.urls import path

from .v1 import views
from .v2 import views as views_v2

urlpatterns = [
    path("create_access", views.ApiPaasView.as_view(), name="create_access"),
    path("create_access_v2", views_v2.ApiPaasViewV2.as_view(), name="create_access_v2"),
    path("groups", views.LDAPGroups.as_view(), name="groups"),
    path("ports", views.UTMService.as_view(), name="services"),
    path("interfaces", views.UTMInterface.as_view(), name="interfaces"),
]
