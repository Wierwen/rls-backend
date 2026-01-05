from django.urls import path
from . import views

urlpatterns = [
    path("me/", views.me, name="patients-me"),
    path("<int:patient_id>/", views.patient_detail),
    path("", views.list_patients),
    path("me/practitioners/", views.my_practitioners),
]
