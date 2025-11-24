from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["GET"])
def list_questionnaires(request):
    # Erstmal nur Dummy-Daten — deine Kollegin kann das erweitern
    return Response({"questionnaires": []})
