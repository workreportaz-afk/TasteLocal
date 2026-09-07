from django.contrib import admin
from .models import Vendor, FoodExperience, Booking, Review, SavedExperience, ItineraryStop, FoodExperienceTranslation


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ["business_name", "user", "cuisine_type", "is_approved", "created_at"]
    list_filter = ["is_approved", "cuisine_type"]
    search_fields = ["business_name", "user__username"]


@admin.register(FoodExperience)
class FoodExperienceAdmin(admin.ModelAdmin):
    list_display = ["title", "vendor", "category", "price", "is_active", "created_at"]
    list_filter = ["category", "is_active"]
    search_fields = ["title", "vendor__business_name"]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["experience", "tourist", "booking_date", "status", "total_price"]
    list_filter = ["status"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["experience", "tourist", "rating", "created_at"]
    list_filter = ["rating"]


@admin.register(SavedExperience)
class SavedExperienceAdmin(admin.ModelAdmin):
    list_display = ["tourist", "experience", "saved_at"]


@admin.register(ItineraryStop)
class ItineraryStopAdmin(admin.ModelAdmin):
    list_display = ["tourist", "experience", "planned_date", "order"]
    list_filter = ["planned_date"]


@admin.register(FoodExperienceTranslation)
class FoodExperienceTranslationAdmin(admin.ModelAdmin):
    list_display = ["experience", "language", "title", "updated_at"]
    list_filter = ["language"]
    search_fields = ["title", "experience__title"]
