"""
Seeds the database with mockup data based on real, well-known Singapore hawker
stalls, restaurants and food tour concepts (sourced from the MICHELIN Guide
Singapore 2026 Bib Gourmand list and general public knowledge of Singapore's
food scene). Intended for demo/testing purposes for the TasteLocal capstone
project -- not for production use, and prices/durations are illustrative.

Usage:
    python manage.py seed_demo_data

Safe to re-run: uses get_or_create throughout, so running it twice won't
create duplicates.
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Vendor, FoodExperience, Booking, Review


VENDORS = [
    {
        "username": "tiantian_vendor",
        "business_name": "Tian Tian Hainanese Chicken Rice",
        "description": (
            "Legendary Maxwell Food Centre stall famous for its silky "
            "Hainanese chicken rice, queued for by locals and tourists alike."
        ),
        "cuisine_type": "Hainanese / Chicken Rice",
        "address": "Maxwell Food Centre, 1 Kadayanallur St, Singapore 069184",
        "latitude": 1.2805, "longitude": 103.8447,
        "phone": "+65 9187 1998",
    },
    {
        "username": "songfa_vendor",
        "business_name": "Song Fa Bak Kut Teh",
        "description": (
            "Flagship New Bridge Road outlet serving peppery pork rib soup, "
            "a Bib Gourmand mainstay since the Michelin Guide's Singapore debut."
        ),
        "cuisine_type": "Teochew / Bak Kut Teh",
        "address": "11 New Bridge Rd, Singapore 059383",
        "latitude": 1.2854, "longitude": 103.8449,
        "phone": "+65 6533 6128",
    },
    {
        "username": "anoodlestory_vendor",
        "business_name": "A Noodle Story",
        "description": (
            "Amoy Street Food Centre stall blending Chinese and Japanese "
            "techniques in its signature mee pok, a decade-long Bib Gourmand holder."
        ),
        "cuisine_type": "Fusion Noodles",
        "address": "Amoy Street Food Centre, 7 Maxwell Rd, Singapore 069111",
        "latitude": 1.2798, "longitude": 103.8477,
        "phone": "+65 8698 4295",
    },
    {
        "username": "bismillah_vendor",
        "business_name": "Bismillah Biryani",
        "description": (
            "Little India institution serving fragrant mutton and chicken "
            "biryani, a Bib Gourmand fixture across all 10 Michelin editions."
        ),
        "cuisine_type": "Indian Muslim / Biryani",
        "address": "50 Dunlop St, Singapore 209379",
        "latitude": 1.3070, "longitude": 103.8517,
        "phone": "+65 6296 9284",
    },
    {
        "username": "sinhuat_vendor",
        "business_name": "Sin Huat Seafood House",
        "description": (
            "Geylang institution known for crab bee hoon and live seafood, "
            "a Bib Gourmand mainstay for fine seafood dining."
        ),
        "cuisine_type": "Seafood / Zi Char",
        "address": "27 Lorong 35 Geylang, Singapore 387934",
        "latitude": 1.3157, "longitude": 103.8886,
        "phone": "+65 6744 9755",
    },
    {
        "username": "cheysua_vendor",
        "business_name": "Chey Sua Carrot Cake",
        "description": (
            "Ang Mo Kio hawker stall serving both black and white carrot "
            "cake, a 10-time Bib Gourmand holder and neighbourhood favourite."
        ),
        "cuisine_type": "Local Breakfast / Carrot Cake",
        "address": "Blk 341 Ang Mo Kio Ave 1, Singapore 560341",
        "latitude": 1.3691, "longitude": 103.8454,
        "phone": "+65 9012 3456",
    },
    {
        "username": "localtrails_vendor",
        "business_name": "Local Food Trails SG",
        "description": (
            "Independent tour operator running guided, small-group food "
            "walks through Singapore's most storied hawker and heritage districts."
        ),
        "cuisine_type": "Guided Food Tours",
        "address": "Singapore (meeting points vary by tour)",
        "latitude": 1.3000, "longitude": 103.8500,
        "phone": "+65 8123 4567",
    },
    {
        "username": "heritageacademy_vendor",
        "business_name": "Heritage Hawker Cooking Academy",
        "description": (
            "Hands-on cooking studio teaching home cooks and visitors how to "
            "recreate Singapore's iconic hawker dishes from scratch."
        ),
        "cuisine_type": "Cooking Classes",
        "address": "instructor-led, Tiong Bahru studio",
        "latitude": 1.2857, "longitude": 103.8267,
        "phone": "+65 8234 5678",
    },
]

# (vendor_username, title, description, category, price, duration_minutes,
#  max_participants, address, lat, lng)
EXPERIENCES = [
    (
        "tiantian_vendor",
        "Tian Tian Hainanese Chicken Rice Tasting",
        "Sample the chicken rice that put Maxwell Food Centre on the "
        "world food map, with silky poached chicken, fragrant rice, and "
        "housemade chilli sauce. A quick, iconic bite for first-time visitors.",
        FoodExperience.Category.TASTING, 12.00, 30, 6,
        "Maxwell Food Centre, 1 Kadayanallur St, Singapore 069184",
        1.2805, 103.8447,
    ),
    (
        "songfa_vendor",
        "Song Fa Bak Kut Teh Signature Tasting",
        "A bowl of Song Fa's peppery, Teochew-style pork rib soup at its "
        "original New Bridge Road shop, paired with youtiao and rice.",
        FoodExperience.Category.TASTING, 15.00, 40, 8,
        "11 New Bridge Rd, Singapore 059383",
        1.2854, 103.8449,
    ),
    (
        "anoodlestory_vendor",
        "A Noodle Story Signature Mee Pok",
        "Try the fusion mee pok that's kept this stall a Bib Gourmand "
        "favourite for over a decade, made fresh at Amoy Street Food Centre.",
        FoodExperience.Category.TASTING, 10.00, 20, 4,
        "Amoy Street Food Centre, 7 Maxwell Rd, Singapore 069111",
        1.2798, 103.8477,
    ),
    (
        "bismillah_vendor",
        "Bismillah Biryani Experience",
        "A plate of fragrant mutton or chicken biryani at a Little India "
        "institution that's held Bib Gourmand status every year since 2016.",
        FoodExperience.Category.TASTING, 14.00, 30, 6,
        "50 Dunlop St, Singapore 209379",
        1.3070, 103.8517,
    ),
    (
        "sinhuat_vendor",
        "Sin Huat Seafood Feast",
        "A shared feast centred on Sin Huat's famous crab bee hoon, plus "
        "live seafood chosen fresh from the tank at this Geylang institution.",
        FoodExperience.Category.FINE_DINING, 80.00, 90, 8,
        "27 Lorong 35 Geylang, Singapore 387934",
        1.3157, 103.8886,
    ),
    (
        "cheysua_vendor",
        "Ang Mo Kio Carrot Cake & Local Breakfast",
        "Start the day the local way: both black and white carrot cake, "
        "plus kopi, at a long-running neighbourhood hawker favourite.",
        FoodExperience.Category.TASTING, 8.00, 20, 6,
        "Blk 341 Ang Mo Kio Ave 1, Singapore 560341",
        1.3691, 103.8454,
    ),
    (
        "localtrails_vendor",
        "Katong Peranakan Food Walk",
        "A guided walk through Katong's pastel shophouses and Peranakan "
        "food heritage: laksa, kueh chang, and the story of the Straits Chinese.",
        FoodExperience.Category.MARKET_TOUR, 58.00, 180, 10,
        "Katong / East Coast Rd, Singapore",
        1.3050, 103.9052,
    ),
    (
        "localtrails_vendor",
        "Chinatown Hawker Heritage Trail",
        "Visit three Bib Gourmand legends in one trail: chicken rice at "
        "Maxwell, noodles at Amoy Street, and zi char in Chinatown's back alleys.",
        FoodExperience.Category.STREET_FOOD, 45.00, 150, 10,
        "Chinatown, Singapore",
        1.2830, 103.8440,
    ),
    (
        "localtrails_vendor",
        "Little India Spice & Biryani Trail",
        "Explore Little India's spice shops and biryani houses, ending at "
        "a Bib Gourmand-recognised biryani institution on Dunlop Street.",
        FoodExperience.Category.MARKET_TOUR, 42.00, 150, 10,
        "Little India, Singapore",
        1.3068, 103.8496,
    ),
    (
        "heritageacademy_vendor",
        "Master Hainanese Chicken Rice At Home",
        "A hands-on class teaching the poaching technique, rice method, "
        "and chilli sauce recipe behind Singapore's national dish.",
        FoodExperience.Category.COOKING_CLASS, 68.00, 120, 8,
        "Tiong Bahru cooking studio, Singapore",
        1.2857, 103.8267,
    ),
]


DEMO_TOURISTS = [
    {"username": "alex_tourist", "email": "alex_tourist@example.com"},
    {"username": "mei_tourist", "email": "mei_tourist@example.com"},
    {"username": "jason_tourist", "email": "jason_tourist@example.com"},
]

# (tourist_username, experience_title, rating, comment, days_ago, participants)
REVIEWS = [
    (
        "alex_tourist", "Tian Tian Hainanese Chicken Rice Tasting", 5,
        "Queued 20 minutes but worth every bit. Chicken was so silky and "
        "the chilli sauce had real kick. First stop for any visitor.",
        14, 2,
    ),
    (
        "mei_tourist", "Song Fa Bak Kut Teh Signature Tasting", 4,
        "Peppery broth was fantastic, though a little saltier than I like. "
        "The youtiao dipped in soup is a must.",
        10, 1,
    ),
    (
        "jason_tourist", "Katong Peranakan Food Walk", 5,
        "Our guide's stories about the Peranakan community made the food "
        "hit differently. The popiah-making demo was a nice hands-on touch.",
        7, 2,
    ),
    (
        "alex_tourist", "Little India Spice & Biryani Trail", 5,
        "Bismillah's biryani alone was worth the trip. Loved learning "
        "about the spices along the way before we got there.",
        3, 1,
    ),
    (
        "mei_tourist", "Master Hainanese Chicken Rice At Home", 4,
        "Great hands-on class, the poaching technique finally makes sense. "
        "Wish we had a bit more time to practice the chilli sauce.",
        21, 1,
    ),
]


class Command(BaseCommand):
    help = "Seed the database with Singapore food/hawker mockup data for demo purposes."

    def handle(self, *args, **options):
        vendor_lookup = {}
        experience_lookup = {}

        for v in VENDORS:
            user, created = User.objects.get_or_create(
                username=v["username"],
                defaults={"email": f"{v['username']}@example.com"},
            )
            if created:
                user.set_password("demo-pass-1234")
                user.save()

            vendor, _ = Vendor.objects.get_or_create(
                user=user,
                defaults={
                    "business_name": v["business_name"],
                    "description": v["description"],
                    "cuisine_type": v["cuisine_type"],
                    "address": v["address"],
                    "latitude": v["latitude"],
                    "longitude": v["longitude"],
                    "phone": v["phone"],
                    "is_approved": True,
                },
            )
            vendor_lookup[v["username"]] = vendor
            self.stdout.write(f"Vendor ready: {vendor.business_name}")

        for (username, title, description, category, price, duration,
             max_participants, address, lat, lng) in EXPERIENCES:
            vendor = vendor_lookup[username]
            experience, created = FoodExperience.objects.get_or_create(
                vendor=vendor,
                title=title,
                defaults={
                    "description": description,
                    "category": category,
                    "price": price,
                    "duration_minutes": duration,
                    "max_participants": max_participants,
                    "address": address,
                    "latitude": lat,
                    "longitude": lng,
                    "is_active": True,
                },
            )
            experience_lookup[title] = experience
            status = "created" if created else "already existed"
            self.stdout.write(f"Experience {status}: {title}")

        tourist_lookup = {}
        for t in DEMO_TOURISTS:
            user, created = User.objects.get_or_create(
                username=t["username"], defaults={"email": t["email"]}
            )
            if created:
                user.set_password("demo-pass-1234")
                user.save()
            tourist_lookup[t["username"]] = user
            self.stdout.write(f"Tourist ready: {user.username}")

        for (username, exp_title, rating, comment, days_ago, participants) in REVIEWS:
            tourist = tourist_lookup[username]
            experience = experience_lookup.get(exp_title)
            if experience is None:
                self.stdout.write(self.style.WARNING(
                    f"Skipping review -- no experience titled '{exp_title}'"
                ))
                continue

            booking_date = timezone.now() - timedelta(days=days_ago)
            booking, _ = Booking.objects.get_or_create(
                experience=experience,
                tourist=tourist,
                booking_date=booking_date,
                defaults={
                    "number_of_participants": participants,
                    "status": Booking.Status.COMPLETED,
                    "total_price": experience.price * participants,
                },
            )
            # Booking might already exist from a previous run but not yet
            # be marked completed -- make sure reviews are always allowed.
            if booking.status != Booking.Status.COMPLETED:
                booking.status = Booking.Status.COMPLETED
                booking.save(update_fields=["status"])

            _, created = Review.objects.get_or_create(
                booking=booking,
                defaults={
                    "experience": experience,
                    "tourist": tourist,
                    "rating": rating,
                    "comment": comment,
                },
            )
            status = "created" if created else "already existed"
            self.stdout.write(f"Review {status}: {tourist.username} -> {exp_title}")

        self.stdout.write(self.style.SUCCESS(
            f"Done: {len(VENDORS)} vendors, {len(EXPERIENCES)} experiences, "
            f"{len(DEMO_TOURISTS)} tourists, {len(REVIEWS)} reviews ready."
        ))
        self.stdout.write(
            "Demo accounts (vendors and tourists) all use password: demo-pass-1234"
        )
