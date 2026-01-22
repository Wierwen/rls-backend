from rest_framework import serializers
from patients.models import PatientConsent
from django.contrib.auth.models import User

class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
class PatientListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
class PatientDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
class PractitionerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class PatientConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientConsent
        fields = [
            "id",
            "patient",
            "practitioner",
            "status",
            "granted_at",
            "revoked_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "granted_at",
            "revoked_at",
            "created_at",
            "updated_at",
        ]


class ConsentActionSerializer(serializers.Serializer):
    practitioner_id = serializers.IntegerField()
