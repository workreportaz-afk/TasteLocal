from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Vendor(models.Model):
    """A local food business / operator who lists experiences on the platform."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vendor_profile"
    )
    business_name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    cuisine_type = models.CharField(max_length=80, blank=True)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    logo = models.ImageField(upload_to="vendor_logos/", null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name


class FoodExperience(models.Model):
    """A bookable food experience: street food tour, cooking class, tasting, etc."""

    class Category(models.TextChoices):
        STREET_FOOD = "street_food", "Street Food Tour"
        FINE_DINING = "fine_dining", "Fine Dining"
        COOKING_CLASS = "cooking_class", "Cooking Class"
        MARKET_TOUR = "market_tour", "Market Tour"
        TASTING = "tasting", "Tasting Session"
        OTHER = "other", "Other"

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="experiences")
    title = models.CharField(max_length=150)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    duration_minutes = models.PositiveIntegerField(default=60)
    max_participants = models.PositiveIntegerField(default=10)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    image = models.ImageField(upload_to="experience_images/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def average_rating(self):
        agg = self.reviews.aggregate(models.Avg("rating"))
        return round(agg["rating__avg"], 1) if agg["rating__avg"] else None


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    experience = models.ForeignKey(FoodExperience, on_delete=models.CASCADE, related_name="bookings")
    tourist = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings"
    )
    booking_date = models.DateTimeField()
    number_of_participants = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_price = models.DecimalField(max_digits=9, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tourist} -> {self.experience} on {self.booking_date:%Y-%m-%d}"

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.experience.price * self.number_of_participants
        super().save(*args, **kwargs)


class Review(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="review")
    experience = models.ForeignKey(FoodExperience, on_delete=models.CASCADE, related_name="reviews")
    tourist = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rating}\u2605 for {self.experience}"


class SavedExperience(models.Model):
    """A tourist's bookmarked ('heart') experience -- the 'Saved Food Spots' feature."""

    tourist = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_experiences"
    )
    experience = models.ForeignKey(FoodExperience, on_delete=models.CASCADE, related_name="saved_by")
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-saved_at"]
        unique_together = ["tourist", "experience"]

    def __str__(self):
        return f"{self.tourist} saved {self.experience}"


class ItineraryStop(models.Model):
    """One stop in a tourist's self-built food itinerary -- 'Plan My Trip'."""

    tourist = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="itinerary_stops"
    )
    experience = models.ForeignKey(FoodExperience, on_delete=models.CASCADE, related_name="itinerary_entries")
    planned_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["planned_date", "order", "added_at"]
        unique_together = ["tourist", "experience"]

    def __str__(self):
        return f"{self.tourist} -> {self.experience} (trip stop)"
