from django.urls import path
from . import views

urlpatterns = [
    path("patients.csv", views.export_assigned_patients_csv, name="export_patients_csv"),
]

