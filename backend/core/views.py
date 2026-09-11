from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Avg, Q
from django.shortcuts import render
from rest_framework import viewsets, permissions, generics, filters, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .geo import haversine_km
from .models import Vendor, FoodExperience, Booking, Review, SavedExperience, ItineraryStop
from .permissions import (
    IsOwnerVendorOrReadOnly, IsOwnVendorProfileOrReadOnly, IsBookingOwner,
    IsVendor, IsVendorOfBooking,
)
from .recommendations import get_recommendations_for_user
from .trip_planner import plan_trip
from .serializers import (
    RegisterSerializer, UserSerializer, VendorSerializer, FoodExperienceListSerializer,
    FoodExperienceDetailSerializer, FoodExperienceWriteSerializer,
    BookingSerializer, VendorBookingStatusSerializer, ReviewSerializer,
    SavedExperienceSerializer, ItineraryStopSerializer,
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
    # IsOwnVendorProfileOrReadOnly stops one vendor from editing another
    # vendor's profile -- previously ANY authenticated user could PATCH/DELETE
    # any /api/vendors/<id>/, which is also how a vendor's own edits could be
    # accidentally clobbered.
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnVendorProfileOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get", "patch"], permission_classes=[permissions.IsAuthenticated, IsVendor])
    def me(self, request):
        """
        GET/PATCH /api/vendors/me/ -- convenience endpoint so the frontend
        doesn't need to already know its own vendor id to edit its stall
        profile (business name, description, address, phone, logo).
        """
        vendor = request.user.vendor_profile
        if request.method == "GET":
            serializer = self.get_serializer(vendor)
            return Response(serializer.data)
        serializer = self.get_serializer(vendor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


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

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def recommended(self, request):
        """
        GET /api/experiences/recommended/
        "Recommended For You" -- content-based ranking from saves/itinerary/
        bookings history, not an ML model or external AI call. See
        core/recommendations.py for the full explanation.
        """
        recommendations = get_recommendations_for_user(request.user, self.get_queryset())
        serializer = FoodExperienceListSerializer(recommendations, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated], url_path="plan-trip")
    def plan_trip_chat(self, request):
        """
        POST /api/experiences/plan-trip/  body: {"message": "..."}
        Rule-based trip planning assistant -- see core/trip_planner.py for
        why this is keyword parsing, not a real LLM.
        """
        message = request.data.get("message", "").strip()
        if not message:
            return Response({"detail": "message is required"}, status=400)

        reply, matched = plan_trip(message, self.get_queryset())
        serializer = FoodExperienceListSerializer(matched, many=True, context=self.get_serializer_context())
        return Response({"reply": reply, "experiences": serializer.data})

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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["experience", "status"]

    def get_queryset(self):
        return Booking.objects.select_related("experience", "tourist").filter(
            tourist=self.request.user
        )


class VendorBookingViewSet(viewsets.GenericViewSet, mixins.ListModelMixin,
                            mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    """
    /api/vendor-bookings/            GET  -- bookings for the logged-in vendor's own experiences
    /api/vendor-bookings/{id}/       GET  -- one booking's detail
    /api/vendor-bookings/{id}/       PATCH {"status": "confirmed"|"cancelled"|"completed"}

    This is what was missing for a vendor to (a) see who has booked their
    stall/experience and (b) confirm or decline a "pending" booking --
    previously there was no vendor-facing booking endpoint at all.
    """

    serializer_class = VendorBookingStatusSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendor, IsVendorOfBooking]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["experience", "status"]

    def get_queryset(self):
        vendor = self.request.user.vendor_profile
        return (
            Booking.objects.select_related("experience", "tourist")
            .filter(experience__vendor=vendor)
            .order_by("-created_at")
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


def home(request):
    """
    Simple landing page at the backend's root URL (e.g. http://localhost:8000/),
    so visiting the API server directly doesn't just 404. Links out to the
    frontend app, the Django admin, and the API root -- mainly a dev-time
    convenience since in production nginx would front both apps together.
    """
    return render(request, "home.html", {
        "frontend_url": settings.FRONTEND_URL,
        "debug": settings.DEBUG,
    })
