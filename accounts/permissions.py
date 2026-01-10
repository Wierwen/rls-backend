from rest_framework.permissions import BasePermission

def _in_group(user, group_name: str) -> bool:
    return bool(user and user.is_authenticated and user.groups.filter(name=group_name).exists())

class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return _in_group(request.user, "patients")

class IsPractitioner(BasePermission):
    def has_permission(self, request, view):
        return _in_group(request.user, "practitioners")

