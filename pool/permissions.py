from rest_framework import permissions
from .models import User

class IsShop(permissions.BasePermission):
    """
    Sadece Dükkan rolündeki kullanıcılar için izin.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.SHOP)

class IsCourier(permissions.BasePermission):
    """
    Sadece Kurye rolündeki kullanıcılar için izin.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.COURIER)

class IsOrderOwner(permissions.BasePermission):
    """
    Siparişin sahibi olan dükkanın erişimine izin verir.
    """
    def has_object_permission(self, request, view, obj):
        return obj.shop == request.user
