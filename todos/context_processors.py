"""Context processors for the todos application."""

from .translations import TRANSLATIONS


def language_context(request):
    """Expose the active language code and translation dictionary to all templates."""
    lang_code = request.session.get("django_language", "en")
    t = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])
    return {
        "lang_code": lang_code,
        "t": t,
    }
