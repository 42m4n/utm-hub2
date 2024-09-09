from django.urls import path

from . import views

urlpatterns = [
    path("v1/lansweeper_data", views.LansweeprView.as_view(), name="lansweeper_data"),
]
