from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from .models import Vendor, FoodExperience, Booking, Review, SavedExperience, ItineraryStop


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    vendor_id = serializers.SerializerMethodField()
    vendor_is_approved = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "role", "vendor_id", "vendor_is_approved",
        ]

    def get_role(self, obj):
        # Three roles: admin (Django staff/superuser), vendor (has a Vendor
        # profile), tourist (everyone else). Checked in this order because a
        # staff account could technically also have a vendor profile.
        if obj.is_staff or obj.is_superuser:
            return "admin"
        if hasattr(obj, "vendor_profile"):
            return "vendor"
        return "tourist"

    def get_vendor_id(self, obj):
        vendor = getattr(obj, "vendor_profile", None)
        return vendor.id if vendor else None

    def get_vendor_is_approved(self, obj):
        vendor = getattr(obj, "vendor_profile", None)
        return vendor.is_approved if vendor else None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    account_type = serializers.ChoiceField(
        choices=["tourist", "vendor"], write_only=True, default="tourist"
    )
    business_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "password", "first_name", "last_name",
            "account_type", "business_name",
        ]

    def validate(self, attrs):
        if attrs.get("account_type") == "vendor" and not attrs.get("business_name"):
            raise serializers.ValidationError(
                {"business_name": "Business name is required for a vendor account."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        account_type = validated_data.pop("account_type", "tourist")
        business_name = validated_data.pop("business_name", "")
        user = User.objects.create_user(**validated_data)
        if account_type == "vendor":
            # New vendors start unapproved -- they go through the same
            # admin-approval gate as any vendor, so their listings stay
            # hidden from public browsing until approved (see
            # FoodExperienceViewSet.get_queryset).
            Vendor.objects.create(user=user, business_name=business_name, is_approved=False)
        return user


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

    def validate(self, attrs):
        # DRF can't auto-generate a unique_together validator here because
        # 'tourist' isn't a writable serializer field (it comes from
        # request.user in create(), not the request body) -- without this,
        # a duplicate save would hit the DB's unique constraint directly and
        # surface as an unhandled 500 IntegrityError instead of a clean 400.
        request = self.context.get("request")
        experience = attrs.get("experience", getattr(self.instance, "experience", None))
        if request and experience:
            qs = SavedExperience.objects.filter(tourist=request.user, experience=experience)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"experience": "You've already saved this experience."})
        return attrs

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

    def validate(self, attrs):
        # Same rationale as SavedExperienceSerializer.validate above.
        request = self.context.get("request")
        experience = attrs.get("experience", getattr(self.instance, "experience", None))
        if request and experience:
            qs = ItineraryStop.objects.filter(tourist=request.user, experience=experience)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"experience": "This experience is already in your trip."})
        return attrs

    def create(self, validated_data):
        validated_data["tourist"] = self.context["request"].user
        return super().create(validated_data)
