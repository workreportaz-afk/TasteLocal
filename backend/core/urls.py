from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import (
    RegisterView, MeView, VendorViewSet, FoodExperienceViewSet, BookingViewSet, ReviewViewSet,
    SavedExperienceViewSet, ItineraryStopViewSet,
)

router = DefaultRouter()
router.register("vendors", VendorViewSet, basename="vendor")
router.register("experiences", FoodExperienceViewSet, basename="experience")
router.register("bookings", BookingViewSet, basename="booking")
router.register("reviews", ReviewViewSet, basename="review")
router.register("saved", SavedExperienceViewSet, basename="saved")
router.register("itinerary", ItineraryStopViewSet, basename="itinerary")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="login"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]
