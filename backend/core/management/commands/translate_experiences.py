from django.core.management.base import BaseCommand

from core.models import FoodExperience
from core.translation import get_or_create_translation, LANGPAIR_TARGET


class Command(BaseCommand):
    help = "Pre-translate all FoodExperience titles/descriptions into every supported language, caching the results so the live site never has to call the translation API during a request."

    def handle(self, *args, **options):
        experiences = FoodExperience.objects.all()
        total = experiences.count()
        languages = list(LANGPAIR_TARGET.keys())

        self.stdout.write(f"Translating {total} experiences into {languages}...")

        created_count = 0
        for index, experience in enumerate(experiences, start=1):
            for lang in languages:
                translation = get_or_create_translation(experience, lang)
                if translation:
                    created_count += 1
            self.stdout.write(f"  [{index}/{total}] {experience.title}")

        self.stdout.write(self.style.SUCCESS(
            f"Done. {created_count} translation(s) created or already cached."
        ))