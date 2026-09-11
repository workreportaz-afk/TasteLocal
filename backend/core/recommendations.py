"""
"Recommended For You" -- a content-based recommendation engine.

This is NOT a machine-learning model and does not call any external AI
service. It's a transparent, explainable ranking: look at which categories
of experience a tourist has shown interest in (via saves, itinerary stops,
and completed bookings), then rank unseen experiences by how well their
category matches that history, tie-broken by rating. New users with no
history get the platform's highest-rated experiences (a standard
"cold start" fallback in recommender systems).

Worth documenting honestly in a capstone writeup as content-based filtering,
a real and well-established recommendation technique -- just not a neural
network or an external AI API.
"""
from collections import Counter

from django.db.models import Q, Case, When, Value, IntegerField

from .models import FoodExperience


def get_recommendations_for_user(user, queryset, limit=4):
    """
    `queryset` should already be filtered to what this user is allowed to
    see (approved vendors, is_active, etc.) -- see FoodExperienceViewSet.
    Returns up to `limit` experiences, best match first.
    """
    interacted_ids = set(
        FoodExperience.objects.filter(
            Q(saved_by__tourist=user) | Q(itinerary_entries__tourist=user) | Q(bookings__tourist=user)
        ).values_list("id", flat=True)
    )

    interest_categories = list(
        FoodExperience.objects.filter(
            Q(saved_by__tourist=user) | Q(itinerary_entries__tourist=user) | Q(bookings__tourist=user)
        ).values_list("category", flat=True)
    )

    candidates = queryset.exclude(id__in=interacted_ids)

    if not interest_categories:
        # Cold start: no saves/bookings/itinerary yet -- surface what's
        # generally well-reviewed instead of guessing at a preference.
        return list(candidates.order_by("-avg_rating", "-created_at")[:limit])

    # Rank categories by how often they show up in this user's history,
    # most-common first, then order candidates to match that preference.
    ranked_categories = [category for category, _ in Counter(interest_categories).most_common()]
    category_rank = Case(
        *[When(category=category, then=Value(rank)) for rank, category in enumerate(ranked_categories)],
        default=Value(len(ranked_categories)),
        output_field=IntegerField(),
    )
    return list(
        candidates.annotate(category_preference_rank=category_rank)
        .order_by("category_preference_rank", "-avg_rating")[:limit]
    )
