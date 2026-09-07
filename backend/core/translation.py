"""
Free, on-the-fly machine translation for experience titles/descriptions.

Uses the MyMemory Translation API (https://mymemory.translated.net/) -- no
API key or signup required for low-volume use (MyMemory's published free
tier is ~5,000 words/day anonymous, which comfortably covers a coursework
project's traffic). This is deliberately NOT the unofficial Google Translate
endpoint some hobby projects scrape (undocumented, can break without notice)
and NOT a self-hosted LibreTranslate container (a multi-GB ML service --
more infrastructure than this project's scale needs).

Results are cached in FoodExperienceTranslation, so each experience is only
translated once per language, ever -- not on every page view. If the API is
slow, down, or returns something unexpected, we fall back to the original
English text rather than let a free third-party service ever break the page.
"""
import requests

MYMEMORY_URL = "https://api.mymemory.translated.net/get"

# MyMemory's language codes for the languages this project supports.
LANGPAIR_TARGET = {
    "zh": "zh-CN",
    "ms": "ms",
}


def translate_text(text, target_lang, source_lang="en", timeout=5):
    """
    Translate `text` from English into `target_lang` ("zh" or "ms").
    Always returns a string -- the original `text` unchanged if translation
    isn't possible for any reason (unsupported language, empty text, the
    API being unreachable, rate-limited, or returning something unexpected).
    """
    if not text or target_lang not in LANGPAIR_TARGET:
        return text

    langpair = f"{source_lang}|{LANGPAIR_TARGET[target_lang]}"
    try:
        response = requests.get(
            MYMEMORY_URL,
            # MyMemory's free tier caps translation quality/reliability on
            # very long input; experience descriptions are short enough
            # that truncation here should never actually trigger in practice.
            params={"q": text[:500], "langpair": langpair},
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        translated = data.get("responseData", {}).get("translatedText")
        return translated or text
    except (requests.RequestException, ValueError, KeyError):
        return text


def get_or_create_translation(experience, lang):
    """
    Return a cached FoodExperienceTranslation for (experience, lang),
    translating and caching it now if it doesn't exist yet. Returns None
    if the language isn't supported, or if translation didn't actually
    produce anything different from the English original (API failure) --
    callers should treat None as "just show the English version".
    """
    from .models import FoodExperienceTranslation  # local import avoids a module-load-time cycle

    if lang not in LANGPAIR_TARGET:
        return None

    cached = FoodExperienceTranslation.objects.filter(experience=experience, language=lang).first()
    if cached:
        return cached

    translated_title = translate_text(experience.title, lang)
    translated_description = translate_text(experience.description, lang)

    if translated_title == experience.title and translated_description == experience.description:
        return None  # translation didn't actually happen -- don't cache a no-op row

    return FoodExperienceTranslation.objects.create(
        experience=experience,
        language=lang,
        title=translated_title,
        description=translated_description,
    )
