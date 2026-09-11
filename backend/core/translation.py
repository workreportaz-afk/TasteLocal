"""
Free, on-the-fly machine translation for experience titles/descriptions.

Uses the MyMemory Translation API (https://mymemory.translated.net/) -- no
API key or signup required for low-volume use (MyMemory's published free
tier is ~5,000 words/day anonymous). This is deliberately NOT the unofficial
Google Translate endpoint some hobby projects scrape (undocumented, can
break without notice) and NOT a self-hosted LibreTranslate container (a
multi-GB ML service -- more infrastructure than this project's scale needs).

Results are cached in FoodExperienceTranslation, so each experience is only
translated once per language, ever -- not on every page view.

CIRCUIT BREAKER: MyMemory's free tier has a real daily quota, and once it's
hit, every request returns an error (HTTP 429). Without a circuit breaker,
a full page of N experiences would retry the API N times on every single
page load once the quota is exhausted -- each one adding real network
latency -- which is exactly what caused this project's homepage to hang on
"Loading experiences..." Once we see a failure, we stop calling the API
entirely for a cooldown period and fall back to English immediately (no
network call at all), so a struggling third-party API can never cascade
into blocking the page for every visitor.
"""
import requests
from django.core.cache import cache

MYMEMORY_URL = "https://api.mymemory.translated.net/get"

# MyMemory's language codes for the languages this project supports.
LANGPAIR_TARGET = {
    "zh": "zh-CN",
    "ms": "ms",
}

_CIRCUIT_BREAKER_CACHE_KEY = "translation_api_unavailable"
_CIRCUIT_BREAKER_COOLDOWN_SECONDS = 60 * 30  # 30 minutes


def translate_text(text, target_lang, source_lang="en", timeout=5):
    """
    Translate `text` from English into `target_lang` ("zh" or "ms").
    Always returns a string -- the original `text` unchanged if translation
    isn't possible for any reason (unsupported language, empty text, the
    circuit breaker being open, or the API being unreachable/rate-limited/
    returning something unexpected).
    """
    if not text or target_lang not in LANGPAIR_TARGET:
        return text

    if cache.get(_CIRCUIT_BREAKER_CACHE_KEY):
        # We've failed recently -- don't even try. This is the fix: fail
        # fast (no network call) instead of retrying a struggling API for
        # every single experience on every single page load.
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

        # MyMemory sometimes returns HTTP 200 with an error embedded in the
        # body (e.g. for some invalid-langpair cases) rather than a proper
        # 4xx -- catch that explicitly too, not just raise_for_status().
        response_status = data.get("responseStatus")
        if response_status and int(response_status) >= 400:
            raise requests.RequestException(data.get("responseDetails", "MyMemory API error"))

        translated = data.get("responseData", {}).get("translatedText")
        return translated or text
    except (requests.RequestException, ValueError, KeyError, TypeError):
        cache.set(_CIRCUIT_BREAKER_CACHE_KEY, True, _CIRCUIT_BREAKER_COOLDOWN_SECONDS)
        return text


def get_or_create_vendor_translation(vendor, lang):
    """
    Same pattern as get_or_create_translation, but for a Vendor's business
    name. See VendorTranslation's docstring for the caveat about machine-
    translating proper nouns -- this exists because it was explicitly
    requested, not because it's guaranteed to read naturally.
    """
    from .models import VendorTranslation  # local import avoids a module-load-time cycle

    if lang not in LANGPAIR_TARGET:
        return None

    cached = VendorTranslation.objects.filter(vendor=vendor, language=lang).first()
    if cached:
        return cached

    translated_name = translate_text(vendor.business_name, lang)
    if translated_name == vendor.business_name:
        return None  # translation didn't actually happen -- don't cache a no-op row

    return VendorTranslation.objects.create(vendor=vendor, language=lang, business_name=translated_name)


def get_or_create_translation(experience, lang):
    """
    Return a cached FoodExperienceTranslation for (experience, lang),
    translating and caching it now if it doesn't exist yet. Returns None
    if the language isn't supported, or if translation didn't actually
    produce anything different from the English original (API failure or
    circuit breaker open) -- callers should treat None as "just show the
    English version".
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
