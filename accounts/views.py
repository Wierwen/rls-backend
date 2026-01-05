from django.shortcuts import render

from django.contrib.auth.models import User, Group
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken



@api_view(['POST'])
def register(request):
    data = request.data

    try:
        user = User.objects.create_user(
            username=data["username"],
            password=data["password"]
        )

        # Default group: patients
        patients_group, _ = Group.objects.get_or_create(name="patients")
        user.groups.add(patients_group)

        return Response(
            {"message": "User created and assigned to patients group"},
            status=status.HTTP_201_CREATED
        )

    except Exception:
        return Response(
            {"error": "User already exists"},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
def login(request):
    data = request.data
    user = User.objects.filter(username=data.get("username")).first()

    if user is None or not user.check_password(data.get("password")):
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    refresh = RefreshToken.for_user(user)
    return Response({
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    })

@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_practitioner(request):
    data = request.data

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return Response({"error": "username and password required"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password)

    practitioners_group, _ = Group.objects.get_or_create(name="practitioners")
    user.groups.add(practitioners_group)

    return Response({"message": "Practitioner created"}, status=status.HTTP_201_CREATED)
