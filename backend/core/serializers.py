from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from .models import Vendor, FoodExperience, Booking, Review, SavedExperience, ItineraryStop


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class VendorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Vendor
        fields = [
            "id", "user", "business_name", "description", "cuisine_type",
            "address", "latitude", "longitude", "phone", "logo",
            "is_approved", "created_at",
        ]
        read_only_fields = ["is_approved"]


class ReviewSerializer(serializers.ModelSerializer):
    tourist = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "booking", "experience", "tourist", "rating", "comment", "created_at"]
        read_only_fields = ["experience", "tourist"]

    def validate_booking(self, booking):
        request = self.context["request"]
        if booking.tourist_id != request.user.id:
            raise serializers.ValidationError("You can only review your own bookings.")
        if booking.status != Booking.Status.COMPLETED:
            raise serializers.ValidationError("You can only review completed experiences.")
        return booking

    def create(self, validated_data):
        booking = validated_data["booking"]
        validated_data["experience"] = booking.experience
        validated_data["tourist"] = self.context["request"].user
        return super().create(validated_data)


class FoodExperienceListSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.business_name", read_only=True)
    average_rating = serializers.SerializerMethodField()
    distance_km = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = FoodExperience
        fields = [
            "id", "title", "category", "price", "duration_minutes",
            "max_participants", "address", "latitude", "longitude",
            "image", "vendor", "vendor_name", "average_rating", "is_active",
            "distance_km",
        ]

    def get_average_rating(self, obj):
        # Prefer the queryset annotation (avg_rating, set by FoodExperienceViewSet)
        # when present -- one aggregate query for the whole page. Falls back to
        # the model's own average_rating property for instances fetched any
        # other way (e.g. nested inside another serializer).
        annotated = getattr(obj, "avg_rating", None)
        if annotated is not None:
            return round(annotated, 1)
        return obj.average_rating


class FoodExperienceDetailSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = FoodExperience
        fields = [
            "id", "vendor", "title", "description", "category", "price",
            "duration_minutes", "max_participants", "address", "latitude",
            "longitude", "image", "is_active", "reviews", "average_rating",
            "created_at",
        ]

    def get_average_rating(self, obj):
        annotated = getattr(obj, "avg_rating", None)
        if annotated is not None:
            return round(annotated, 1)
        return obj.average_rating


class FoodExperienceWriteSerializer(serializers.ModelSerializer):
    """Used by vendors to create/update their own experiences."""

    class Meta:
        model = FoodExperience
        fields = [
            "id", "title", "description", "category", "price",
            "duration_minutes", "max_participants", "address",
            "latitude", "longitude", "image", "is_active",
        ]

    def create(self, validated_data):
        request = self.context["request"]
        vendor = getattr(request.user, "vendor_profile", None)
        if vendor is None:
            raise serializers.ValidationError("Only vendors can create experiences.")
        validated_data["vendor"] = vendor
        return super().create(validated_data)


class BookingSerializer(serializers.ModelSerializer):
    tourist = UserSerializer(read_only=True)
    experience_title = serializers.CharField(source="experience.title", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "experience", "experience_title", "tourist", "booking_date",
            "number_of_participants", "status", "total_price", "created_at",
        ]
        read_only_fields = ["status", "total_price"]

    def validate(self, attrs):
        experience = attrs.get("experience") or getattr(self.instance, "experience", None)
        participants = attrs.get(
            "number_of_participants",
            getattr(self.instance, "number_of_participants", 1),
        )
        if experience and participants > experience.max_participants:
            raise serializers.ValidationError(
                f"This experience allows a maximum of {experience.max_participants} participants."
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data["tourist"] = self.context["request"].user
        experience = validated_data["experience"]
        validated_data["total_price"] = experience.price * validated_data["number_of_participants"]
        return super().create(validated_data)


class SavedExperienceSerializer(serializers.ModelSerializer):
    experience_detail = FoodExperienceListSerializer(source="experience", read_only=True)

    class Meta:
        model = SavedExperience
        fields = ["id", "experience", "experience_detail", "saved_at"]
        read_only_fields = ["saved_at"]

    def create(self, validated_data):
        validated_data["tourist"] = self.context["request"].user
        return super().create(validated_data)


class ItineraryStopSerializer(serializers.ModelSerializer):
    experience_detail = FoodExperienceListSerializer(source="experience", read_only=True)

    class Meta:
        model = ItineraryStop
        fields = [
            "id", "experience", "experience_detail", "planned_date",
            "notes", "order", "added_at",
        ]
        read_only_fields = ["added_at"]

    def create(self, validated_data):
        validated_data["tourist"] = self.context["request"].user
        return super().create(validated_data)
