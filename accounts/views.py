from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

@api_view(['POST'])
def register(request):
    data = request.data
    try:
        User.objects.create_user(
            username=data["username"],
            password=data["password"]
        )
        return Response({"message": "User created"}, status=status.HTTP_201_CREATED)
    except:
        return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login(request):
    data = request.data
    user = User.objects.filter(username=data.get("username")).first()
    if user is None or not user.check_password(data.get("password")):
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    return Response({
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    })
