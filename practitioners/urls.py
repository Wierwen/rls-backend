from django.urls import path
from . import views

urlpatterns = [
    path("me/", views.me),
    path("assign-patient/", views.assign_patient),
    path("unassign-patient/", views.unassign_patient),
]

