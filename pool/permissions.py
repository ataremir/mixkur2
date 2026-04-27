from rest_framework import permissions
from .models import User

class IsRestaurant(permissions.BasePermission):
    """
    Sadece Restoran rolündeki kullanıcılar için izin.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.RESTAURANT)

class IsCourier(permissions.BasePermission):
    """
    Sadece Kurye rolündeki kullanıcılar için izin.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.COURIER)

class IsOrderOwner(permissions.BasePermission):
    """
    Siparişin sahibi olan restoranın erişimine izin verir.
    """
    def has_object_permission(self, request, view, obj):
        return obj.restaurant == request.user
