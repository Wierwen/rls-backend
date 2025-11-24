from django.urls import path
from . import views

urlpatterns = [
    # Liste aller Questionnaires
    path('', views.list_questionnaires),
]
