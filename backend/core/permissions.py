from rest_framework import permissions


class IsOwnerVendorOrReadOnly(permissions.BasePermission):
    """Only the vendor who owns an experience may edit/delete it."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        vendor = getattr(request.user, "vendor_profile", None)
        return bool(vendor) and obj.vendor_id == vendor.id


class IsOwnVendorProfileOrReadOnly(permissions.BasePermission):
    """
    Only the vendor who owns a Vendor profile may edit/delete it -- this was
    previously missing, so any authenticated user could PATCH/DELETE any
    vendor's profile via /api/vendors/<id>/. This is what lets a vendor edit
    their own "stall" (business name, description, address, phone, logo).
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user_id == request.user.id


class IsBookingOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.tourist_id == request.user.id


class IsVendor(permissions.BasePermission):
    """Request user has an approved-or-not Vendor profile."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, "vendor_profile"))


class IsVendorOfBooking(permissions.BasePermission):
    """Only the vendor who owns the booking's experience may view/update it."""

    def has_object_permission(self, request, view, obj):
        vendor = getattr(request.user, "vendor_profile", None)
        return bool(vendor) and obj.experience.vendor_id == vendor.id
