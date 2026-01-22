from django.urls import path
from patients import consent_views

from . import views

urlpatterns = [
    path("me/", views.me, name="patients-me"),
    path("<int:patient_id>/", views.patient_detail),
    path("", views.list_patients),
    path("me/practitioners/", views.my_practitioners),
]
urlpatterns += [
    path("consents/", consent_views.list_my_consents),
    path("consents/grant/", consent_views.grant_consent),
    path("consents/revoke/", consent_views.revoke_consent),
]