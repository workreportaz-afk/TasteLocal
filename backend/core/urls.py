from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterView, MeView, VendorViewSet, FoodExperienceViewSet, BookingViewSet,
    VendorBookingViewSet, ReviewViewSet, SavedExperienceViewSet, ItineraryStopViewSet,
)

router = DefaultRouter()
router.register("vendors", VendorViewSet, basename="vendor")
router.register("experiences", FoodExperienceViewSet, basename="experience")
router.register("bookings", BookingViewSet, basename="booking")
router.register("vendor-bookings", VendorBookingViewSet, basename="vendor-booking")
router.register("reviews", ReviewViewSet, basename="review")
router.register("saved", SavedExperienceViewSet, basename="saved")
router.register("itinerary", ItineraryStopViewSet, basename="itinerary")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="login"),
    # Was missing entirely -- the frontend already calls this on a 401 to
    # silently refresh an expired access token (see frontend/src/api/client.js),
    # but it 404'd, so users got logged out abruptly instead.
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]
