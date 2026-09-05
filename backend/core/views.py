from django.contrib.auth.models import User
from django.db.models import Avg, Q
from rest_framework import viewsets, permissions, generics, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .geo import haversine_km
from .models import Vendor, FoodExperience, Booking, Review, SavedExperience, ItineraryStop
from .permissions import IsOwnerVendorOrReadOnly, IsBookingOwner
from .serializers import (
    RegisterSerializer, UserSerializer, VendorSerializer, FoodExperienceListSerializer,
    FoodExperienceDetailSerializer, FoodExperienceWriteSerializer,
    BookingSerializer, ReviewSerializer, SavedExperienceSerializer, ItineraryStopSerializer,
)


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ -- open sign-up for tourists (and vendors)."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    """GET /api/auth/me/ -- returns the currently logged-in user, from the JWT."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.select_related("user").all()
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FoodExperienceViewSet(viewsets.ModelViewSet):
    """
    /api/experiences/            GET (list, public) | POST (vendor only)
    /api/experiences/{id}/       GET (detail, public) | PUT/PATCH/DELETE (owning vendor)
    Supports ?category=street_food, ?vendor=<id>, ?search=noodles, ?ordering=price
    Supports ?near=<lat>,<lng>&radius_km=<n> for "near me" search (default radius 5km),
    which sorts results by distance and adds a distance_km field to each result.
    Free -- distance is computed with the haversine formula, no external API.
    """

    queryset = (
        FoodExperience.objects.select_related("vendor")
        .prefetch_related("reviews")
        .annotate(avg_rating=Avg("reviews__rating"))
        .filter(is_active=True)
    )
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerVendorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "vendor"]
    search_fields = ["title", "description", "vendor__business_name"]
    ordering_fields = ["price", "created_at", "avg_rating"]

    def get_queryset(self):
        qs = self.queryset
        user = self.request.user
        if user.is_authenticated and hasattr(user, "vendor_profile"):
            # A vendor can always see their own listings, even before approval --
            # everyone else only sees listings from approved vendors.
            qs = qs.filter(Q(vendor__is_approved=True) | Q(vendor=user.vendor_profile))
        else:
            qs = qs.filter(vendor__is_approved=True)
        # Explicit ordering: annotate() + the default Meta ordering can leave
        # DRF's paginator unsure the result is deterministic across pages.
        return qs.order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "list":
            return FoodExperienceListSerializer
        if self.action in ("create", "update", "partial_update"):
            return FoodExperienceWriteSerializer
        return FoodExperienceDetailSerializer

    def list(self, request, *args, **kwargs):
        near = request.query_params.get("near")
        if not near:
            return super().list(request, *args, **kwargs)

        try:
            lat_str, lng_str = near.split(",")
            origin_lat, origin_lng = float(lat_str), float(lng_str)
        except (ValueError, AttributeError):
            return Response(
                {"detail": "`near` must be `lat,lng`, e.g. ?near=1.3521,103.8198"},
                status=400,
            )
        radius_km = float(request.query_params.get("radius_km", 5))

        # Geo-filtering happens in Python after the normal filters/search/category
        # narrowing -- fine at this project's scale, and keeps us free of MySQL
        # spatial-index setup, which is unnecessary complexity for a coursework MVP.
        queryset = self.filter_queryset(self.get_queryset()).exclude(
            latitude__isnull=True, longitude__isnull=True
        )

        nearby = []
        for experience in queryset:
            distance = haversine_km(origin_lat, origin_lng, experience.latitude, experience.longitude)
            if distance <= radius_km:
                experience.distance_km = round(distance, 2)
                nearby.append(experience)
        nearby.sort(key=lambda e: e.distance_km)

        page = self.paginate_queryset(nearby)
        serializer = self.get_serializer(page if page is not None else nearby, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class BookingViewSet(viewsets.ModelViewSet):
    """Tourists see and manage only their own bookings."""

    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsBookingOwner]

    def get_queryset(self):
        return Booking.objects.select_related("experience", "tourist").filter(
            tourist=self.request.user
        )


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Review.objects.select_related("tourist", "experience")
        experience_id = self.request.query_params.get("experience")
        if experience_id:
            qs = qs.filter(experience_id=experience_id)
        return qs


class SavedExperienceViewSet(viewsets.ModelViewSet):
    """
    A tourist's bookmarked experiences ('Saved Food Spots').
    POST {"experience": <id>} to save; DELETE /api/saved/<id>/ to un-save.
    """

    serializer_class = SavedExperienceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedExperience.objects.select_related("experience", "experience__vendor").filter(
            tourist=self.request.user
        )


class ItineraryStopViewSet(viewsets.ModelViewSet):
    """
    A tourist's self-planned trip ('Plan My Trip'). Each stop links to one
    experience, optionally with a planned date and personal notes.
    """

    serializer_class = ItineraryStopSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ItineraryStop.objects.select_related("experience", "experience__vendor").filter(
            tourist=self.request.user
        )
