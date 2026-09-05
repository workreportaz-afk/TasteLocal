from rest_framework import permissions


class IsOwnerVendorOrReadOnly(permissions.BasePermission):
    """Only the vendor who owns an experience may edit/delete it."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        vendor = getattr(request.user, "vendor_profile", None)
        return bool(vendor) and obj.vendor_id == vendor.id


class IsBookingOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.tourist_id == request.user.id
