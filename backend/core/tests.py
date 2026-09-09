from decimal import Decimal
from unittest.mock import patch

import requests
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from core.models import Vendor, FoodExperience, Booking, Review, SavedExperience, ItineraryStop, FoodExperienceTranslation


class VendorAndExperienceModelTests(APITestCase):
    def setUp(self):
        self.vendor_user = User.objects.create_user(username="vendoruser", password="pass12345")
        self.vendor = Vendor.objects.create(
            user=self.vendor_user,
            business_name="Test Hawker Stall",
            cuisine_type="Street Food",
        )
        self.experience = FoodExperience.objects.create(
            vendor=self.vendor,
            title="Sample Food Tour",
            description="A test experience.",
            category=FoodExperience.Category.STREET_FOOD,
            price=Decimal("20.00"),
            max_participants=5,
        )

    def test_booking_total_price_auto_calculated(self):
        tourist = User.objects.create_user(username="touristuser", password="pass12345")
        booking = Booking.objects.create(
            experience=self.experience,
            tourist=tourist,
            booking_date=timezone.now(),
            number_of_participants=3,
        )
        self.assertEqual(booking.total_price, Decimal("60.00"))

    def test_average_rating_none_without_reviews(self):
        self.assertIsNone(self.experience.average_rating)

    def test_average_rating_reflects_reviews(self):
        tourist = User.objects.create_user(username="reviewer", password="pass12345")
        booking = Booking.objects.create(
            experience=self.experience,
            tourist=tourist,
            booking_date=timezone.now(),
            number_of_participants=1,
            status=Booking.Status.COMPLETED,
        )
        Review.objects.create(booking=booking, experience=self.experience, tourist=tourist, rating=4)
        experience = FoodExperience.objects.filter(pk=self.experience.pk).first()
        self.assertEqual(experience.average_rating, 4.0)


class ExperienceAPITests(APITestCase):
    def setUp(self):
        vendor_user = User.objects.create_user(username="vendoruser2", password="pass12345")
        vendor = Vendor.objects.create(user=vendor_user, business_name="API Test Vendor", is_approved=True)
        FoodExperience.objects.create(
            vendor=vendor,
            title="Public Listing",
            description="Visible to everyone.",
            category=FoodExperience.Category.TASTING,
            price=Decimal("10.00"),
        )

    def test_experience_list_is_publicly_readable(self):
        response = self.client.get("/api/experiences/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_creating_experience_requires_authentication(self):
        response = self.client.post("/api/experiences/", {
            "title": "Should Fail",
            "description": "No auth provided.",
            "category": "tasting",
            "price": "5.00",
        })
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


class AuthAPITests(APITestCase):
    def test_register_and_login_flow(self):
        register_response = self.client.post("/api/auth/register/", {
            "username": "newtourist",
            "email": "newtourist@example.com",
            "password": "a-strong-password-123",
        })
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        login_response = self.client.post("/api/auth/login/", {
            "username": "newtourist",
            "password": "a-strong-password-123",
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)
        self.assertIn("refresh", login_response.data)


class ExperienceListRatingAnnotationTests(APITestCase):
    """
    Regression test: FoodExperience.average_rating is both a model @property
    and, separately, the field the API list/detail views expose. The
    queryset annotation used to be named 'average_rating' too, which
    collided with the read-only property. This confirms the fix holds:
    the endpoint must not error, and must return a correct rating.
    """

    def test_list_endpoint_with_reviewed_experience_does_not_error(self):
        vendor_user = User.objects.create_user(username="ratingvendor", password="pass12345")
        vendor = Vendor.objects.create(user=vendor_user, business_name="Rating Test Vendor", is_approved=True)
        experience = FoodExperience.objects.create(
            vendor=vendor, title="Rated Experience", description="x",
            category=FoodExperience.Category.TASTING, price=Decimal("10.00"),
        )
        tourist = User.objects.create_user(username="ratingtourist", password="pass12345")
        booking = Booking.objects.create(
            experience=experience, tourist=tourist, booking_date=timezone.now(),
            number_of_participants=1, status=Booking.Status.COMPLETED,
        )
        Review.objects.create(booking=booking, experience=experience, tourist=tourist, rating=5)

        response = self.client.get("/api/experiences/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = next(r for r in response.data["results"] if r["id"] == experience.id)
        self.assertEqual(result["average_rating"], 5.0)


class GeolocationSearchTests(APITestCase):
    def setUp(self):
        vendor_user = User.objects.create_user(username="geovendor", password="pass12345")
        vendor = Vendor.objects.create(user=vendor_user, business_name="Geo Vendor", is_approved=True)
        # Marina Bay Sands, Singapore
        self.near_experience = FoodExperience.objects.create(
            vendor=vendor, title="Near Marina Bay", description="x",
            category=FoodExperience.Category.TASTING, price=Decimal("10.00"),
            latitude=Decimal("1.2834"), longitude=Decimal("103.8607"),
        )
        # Woodlands, Singapore -- roughly 20km from Marina Bay
        self.far_experience = FoodExperience.objects.create(
            vendor=vendor, title="Far in Woodlands", description="x",
            category=FoodExperience.Category.TASTING, price=Decimal("10.00"),
            latitude=Decimal("1.4360"), longitude=Decimal("103.7860"),
        )

    def test_near_filters_out_distant_experiences(self):
        response = self.client.get("/api/experiences/?near=1.2834,103.8607&radius_km=5")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in response.data["results"]]
        self.assertIn(self.near_experience.id, ids)
        self.assertNotIn(self.far_experience.id, ids)

    def test_near_requires_valid_format(self):
        response = self.client.get("/api/experiences/?near=not-a-coordinate")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SavedExperienceTests(APITestCase):
    def setUp(self):
        vendor_user = User.objects.create_user(username="savevendor", password="pass12345")
        vendor = Vendor.objects.create(user=vendor_user, business_name="Save Vendor", is_approved=True)
        self.experience = FoodExperience.objects.create(
            vendor=vendor, title="Saveable", description="x",
            category=FoodExperience.Category.TASTING, price=Decimal("10.00"),
        )
        self.tourist = User.objects.create_user(username="saver", password="pass12345")

    def test_requires_authentication(self):
        response = self.client.post("/api/saved/", {"experience": self.experience.id})
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_can_save_and_list_own_saved_experiences(self):
        self.client.force_authenticate(self.tourist)
        response = self.client.post("/api/saved/", {"experience": self.experience.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        list_response = self.client.get("/api/saved/")
        self.assertEqual(list_response.data["count"], 1)

    def test_cannot_save_the_same_experience_twice(self):
        self.client.force_authenticate(self.tourist)
        self.client.post("/api/saved/", {"experience": self.experience.id})
        response = self.client.post("/api/saved/", {"experience": self.experience.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ItineraryStopTests(APITestCase):
    def setUp(self):
        vendor_user = User.objects.create_user(username="tripvendor", password="pass12345")
        vendor = Vendor.objects.create(user=vendor_user, business_name="Trip Vendor", is_approved=True)
        self.experience = FoodExperience.objects.create(
            vendor=vendor, title="Trip Stop", description="x",
            category=FoodExperience.Category.TASTING, price=Decimal("10.00"),
        )
        self.tourist = User.objects.create_user(username="tripper", password="pass12345")

    def test_can_add_and_list_itinerary_stop(self):
        self.client.force_authenticate(self.tourist)
        response = self.client.post("/api/itinerary/", {
            "experience": self.experience.id,
            "notes": "Try the laksa here",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        list_response = self.client.get("/api/itinerary/")
        self.assertEqual(list_response.data["count"], 1)
        self.assertEqual(list_response.data["results"][0]["notes"], "Try the laksa here")

    def test_cannot_add_the_same_experience_to_trip_twice(self):
        self.client.force_authenticate(self.tourist)
        self.client.post("/api/itinerary/", {"experience": self.experience.id})
        response = self.client.post("/api/itinerary/", {"experience": self.experience.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class VendorApprovalGateTests(APITestCase):
    def setUp(self):
        approved_user = User.objects.create_user(username="approvedvendor", password="pass12345")
        self.approved_vendor = Vendor.objects.create(
            user=approved_user, business_name="Approved Vendor", is_approved=True
        )
        pending_user = User.objects.create_user(username="pendingvendor", password="pass12345")
        self.pending_vendor = Vendor.objects.create(
            user=pending_user, business_name="Pending Vendor", is_approved=False
        )
        self.pending_user = pending_user

        self.approved_experience = FoodExperience.objects.create(
            vendor=self.approved_vendor, title="Visible Listing", description="x",
            category=FoodExperience.Category.TASTING, price=Decimal("10.00"),
        )
        self.pending_experience = FoodExperience.objects.create(
            vendor=self.pending_vendor, title="Hidden Listing", description="x",
            category=FoodExperience.Category.TASTING, price=Decimal("10.00"),
        )

    def test_public_list_excludes_unapproved_vendor_listings(self):
        response = self.client.get("/api/experiences/")
        ids = [r["id"] for r in response.data["results"]]
        self.assertIn(self.approved_experience.id, ids)
        self.assertNotIn(self.pending_experience.id, ids)

    def test_pending_vendor_can_still_see_their_own_listing(self):
        self.client.force_authenticate(self.pending_user)
        response = self.client.get("/api/experiences/")
        ids = [r["id"] for r in response.data["results"]]
        self.assertIn(self.pending_experience.id, ids)


class RoleAndVendorRegistrationTests(APITestCase):
    def test_default_registration_is_tourist_role(self):
        self.client.post("/api/auth/register/", {
            "username": "plaintourist", "email": "t@example.com", "password": "a-strong-password-123",
        })
        login = self.client.post("/api/auth/login/", {
            "username": "plaintourist", "password": "a-strong-password-123",
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        me = self.client.get("/api/auth/me/")
        self.assertEqual(me.data["role"], "tourist")
        self.assertIsNone(me.data["vendor_id"])

    def test_vendor_registration_creates_unapproved_vendor_profile(self):
        response = self.client.post("/api/auth/register/", {
            "username": "newvendor", "email": "v@example.com", "password": "a-strong-password-123",
            "account_type": "vendor", "business_name": "New Vendor Stall",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        vendor = Vendor.objects.get(user__username="newvendor")
        self.assertEqual(vendor.business_name, "New Vendor Stall")
        self.assertFalse(vendor.is_approved)

        login = self.client.post("/api/auth/login/", {
            "username": "newvendor", "password": "a-strong-password-123",
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        me = self.client.get("/api/auth/me/")
        self.assertEqual(me.data["role"], "vendor")
        self.assertEqual(me.data["vendor_id"], vendor.id)
        self.assertFalse(me.data["vendor_is_approved"])

    def test_vendor_registration_requires_business_name(self):
        response = self.client.post("/api/auth/register/", {
            "username": "novendorname", "email": "x@example.com", "password": "a-strong-password-123",
            "account_type": "vendor",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_user_has_admin_role(self):
        admin_user = User.objects.create_user(username="staffuser", password="pass12345", is_staff=True)
        self.client.force_authenticate(admin_user)
        me = self.client.get("/api/auth/me/")
        self.assertEqual(me.data["role"], "admin")


class TranslationCachingTests(APITestCase):
    def setUp(self):
        # The translation circuit breaker lives in Django's cache, which
        # persists across test methods in the same run -- clear it so one
        # test's simulated API failure can't silently trip the breaker for
        # every test that runs after it.
        cache.clear()
        vendor_user = User.objects.create_user(username="translatevendor", password="pass12345")
        vendor = Vendor.objects.create(user=vendor_user, business_name="Translate Vendor", is_approved=True)
        self.experience = FoodExperience.objects.create(
            vendor=vendor, title="Test Dish", description="A tasty test description.",
            category=FoodExperience.Category.TASTING, price=Decimal("10.00"),
        )

    def test_no_lang_param_returns_english(self):
        response = self.client.get(f"/api/experiences/{self.experience.id}/")
        self.assertEqual(response.data["title"], "Test Dish")

    @patch("core.translation.requests.get")
    def test_translation_is_cached_after_first_request(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.raise_for_status = lambda: None
        mock_response.json.return_value = {"responseData": {"translatedText": "测试菜肴"}}

        # First call: cache miss -- should call the (mocked) API for both
        # title and description, then persist a FoodExperienceTranslation row.
        response = self.client.get(f"/api/experiences/{self.experience.id}/?lang=zh")
        self.assertEqual(response.data["title"], "测试菜肴")
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(FoodExperienceTranslation.objects.count(), 1)

        # Second call: cache hit -- must NOT call the API again.
        response = self.client.get(f"/api/experiences/{self.experience.id}/?lang=zh")
        self.assertEqual(response.data["title"], "测试菜肴")
        self.assertEqual(mock_get.call_count, 2)

    @patch("core.translation.requests.get")
    def test_falls_back_to_english_when_translation_api_is_down(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("network down")
        response = self.client.get(f"/api/experiences/{self.experience.id}/?lang=zh")
        self.assertEqual(response.data["title"], "Test Dish")
        self.assertEqual(FoodExperienceTranslation.objects.count(), 0)

    @patch("core.translation.requests.get")
    def test_list_endpoint_also_translates_title(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.raise_for_status = lambda: None
        mock_response.json.return_value = {"responseData": {"translatedText": "测试菜肴"}}

        response = self.client.get("/api/experiences/?lang=zh")
        result = next(r for r in response.data["results"] if r["id"] == self.experience.id)
        self.assertEqual(result["title"], "测试菜肴")

    @patch("core.translation.requests.get")
    def test_circuit_breaker_stops_hammering_a_failing_api(self, mock_get):
        """
        Regression test for the real production incident this project hit:
        MyMemory's free daily quota ran out (HTTP 429), and because
        failures weren't being remembered, EVERY experience on the homepage
        retried the API on EVERY page load -- the accumulated latency of
        many failed sequential calls is what caused the page to hang.
        This confirms the fix: after the first failure, the breaker trips
        and no further network calls are made for other experiences,
        regardless of language or which experience is being translated.
        """
        mock_response = mock_get.return_value
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Too Many Requests")

        second_vendor_user = User.objects.create_user(username="secondtranslatevendor", password="pass12345")
        second_vendor = Vendor.objects.create(
            user=second_vendor_user, business_name="Second Translate Vendor", is_approved=True
        )
        second_experience = FoodExperience.objects.create(
            vendor=second_vendor, title="Another Dish", description="Another description.",
            category=FoodExperience.Category.TASTING, price=Decimal("15.00"),
        )

        # First experience: title translation is attempted first and fails,
        # tripping the breaker immediately. The description translation
        # attempt that follows right after (still within the same
        # get_or_create_translation() call) already sees the tripped
        # breaker and skips the network -- so only ONE real call happens
        # per experience, not two. That's the circuit breaker working even
        # faster than a naive "trip after N failures" design would.
        self.client.get(f"/api/experiences/{self.experience.id}/?lang=zh")
        calls_after_first_experience = mock_get.call_count
        self.assertEqual(calls_after_first_experience, 1)

        # Second, DIFFERENT experience, same request cycle as a fresh page
        # load would make: the breaker should already be open, so this
        # must make ZERO additional calls.
        response = self.client.get(f"/api/experiences/{second_experience.id}/?lang=zh")
        self.assertEqual(mock_get.call_count, calls_after_first_experience)  # unchanged
        self.assertEqual(response.data["title"], "Another Dish")  # fell back to English, not stuck/broken


class RecommendationsTests(APITestCase):
    def setUp(self):
        vendor_user = User.objects.create_user(username="recvendor", password="pass12345")
        self.vendor = Vendor.objects.create(user=vendor_user, business_name="Rec Vendor", is_approved=True)

        self.street_food_1 = FoodExperience.objects.create(
            vendor=self.vendor, title="Street Food A", description="x",
            category=FoodExperience.Category.STREET_FOOD, price=Decimal("10.00"),
        )
        self.street_food_2 = FoodExperience.objects.create(
            vendor=self.vendor, title="Street Food B", description="x",
            category=FoodExperience.Category.STREET_FOOD, price=Decimal("12.00"),
        )
        self.fine_dining = FoodExperience.objects.create(
            vendor=self.vendor, title="Fancy Dinner", description="x",
            category=FoodExperience.Category.FINE_DINING, price=Decimal("80.00"),
        )
        self.tourist = User.objects.create_user(username="rectourist", password="pass12345")

    def test_requires_authentication(self):
        response = self.client.get("/api/experiences/recommended/")
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_cold_start_returns_something_for_new_user(self):
        self.client.force_authenticate(self.tourist)
        response = self.client.get("/api/experiences/recommended/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_prefers_categories_from_saved_history(self):
        self.client.force_authenticate(self.tourist)
        # Tourist saves a street food experience -- recommendations should
        # then favour the OTHER street food experience over fine dining.
        self.client.post("/api/saved/", {"experience": self.street_food_1.id})

        response = self.client.get("/api/experiences/recommended/")
        result_ids = [r["id"] for r in response.data]

        self.assertNotIn(self.street_food_1.id, result_ids)  # already saved, shouldn't recommend it again
        self.assertIn(self.street_food_2.id, result_ids)
        # The matching-category experience should rank above fine dining.
        self.assertLess(result_ids.index(self.street_food_2.id), result_ids.index(self.fine_dining.id))


class TripPlannerChatTests(APITestCase):
    def setUp(self):
        vendor_user = User.objects.create_user(username="tripplannervendor", password="pass12345")
        vendor = Vendor.objects.create(user=vendor_user, business_name="Trip Planner Vendor", is_approved=True)

        self.cheap_street_food = FoodExperience.objects.create(
            vendor=vendor, title="Cheap Eats", description="x",
            category=FoodExperience.Category.STREET_FOOD, price=Decimal("8.00"),
            address="123 Chinatown Street, Singapore",
        )
        self.pricey_fine_dining = FoodExperience.objects.create(
            vendor=vendor, title="Expensive Dinner", description="x",
            category=FoodExperience.Category.FINE_DINING, price=Decimal("120.00"),
            address="456 Orchard Road, Singapore",
        )
        self.tourist = User.objects.create_user(username="chattourist", password="pass12345")

    def test_requires_authentication(self):
        response = self.client.post("/api/experiences/plan-trip/", {"message": "street food"})
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_empty_message_is_rejected(self):
        self.client.force_authenticate(self.tourist)
        response = self.client.post("/api/experiences/plan-trip/", {"message": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_category_keyword_filters_correctly(self):
        self.client.force_authenticate(self.tourist)
        response = self.client.post("/api/experiences/plan-trip/", {"message": "I want street food"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [e["id"] for e in response.data["experiences"]]
        self.assertIn(self.cheap_street_food.id, result_ids)
        self.assertNotIn(self.pricey_fine_dining.id, result_ids)

    def test_budget_keyword_filters_correctly(self):
        self.client.force_authenticate(self.tourist)
        response = self.client.post("/api/experiences/plan-trip/", {"message": "something under $20"})
        result_ids = [e["id"] for e in response.data["experiences"]]
        self.assertIn(self.cheap_street_food.id, result_ids)
        self.assertNotIn(self.pricey_fine_dining.id, result_ids)

    def test_area_keyword_filters_correctly(self):
        self.client.force_authenticate(self.tourist)
        response = self.client.post("/api/experiences/plan-trip/", {"message": "food near Chinatown"})
        result_ids = [e["id"] for e in response.data["experiences"]]
        self.assertIn(self.cheap_street_food.id, result_ids)
        self.assertNotIn(self.pricey_fine_dining.id, result_ids)

    def test_no_match_returns_helpful_reply(self):
        self.client.force_authenticate(self.tourist)
        response = self.client.post("/api/experiences/plan-trip/", {"message": "fine dining under $5"})
        self.assertEqual(response.data["experiences"], [])
        self.assertIn("couldn't find", response.data["reply"])


class BackendHomePageTests(APITestCase):
    def test_home_page_loads_and_links_to_frontend_and_admin(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"/admin/", response.content)
        self.assertIn(b"/api/experiences/", response.content)
