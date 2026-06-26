#!/usr/bin/env python3
"""AsimNexus Multi-language Support - Nepal Localization"""
from typing import Dict, Any, Optional


class LanguageManager:
    """Manages multi-language support for Nepal (Nepali, English, regional)."""

    SUPPORTED_LANGUAGES = ["ne", "en", "mai", "bho", "doo"]  # Nepali, English, Maithili, Bhojpuri, Doteli

    def __init__(self):
        self.current_language = "ne"
        self.translations: Dict[str, Dict[str, str]] = {
            "ne": {"hello": "नमस्ते", "world": "संसार", "welcome": "स्वागत छ"},
            "en": {"hello": "Hello", "world": "World", "welcome": "Welcome"},
            "mai": {"hello": "नमस्ते", "world": "दुनिया", "welcome": "स्वागत"},
        }

    def set_language(self, lang_code: str) -> Dict[str, Any]:
        """Set current language."""
        if lang_code in self.SUPPORTED_LANGUAGES:
            self.current_language = lang_code
            return {"status": "success", "language": lang_code}
        return {"status": "error", "error": f"Unsupported language: {lang_code}"}

    def translate(self, key: str, lang: Optional[str] = None) -> str:
        """Translate a key to the current or specified language."""
        lang = lang or self.current_language
        return self.translations.get(lang, {}).get(key, key)

    def get_supported_languages(self) -> list:
        """Get list of supported language codes."""
        return self.SUPPORTED_LANGUAGES

    def get_status(self) -> Dict[str, Any]:
        return {
            "current_language": self.current_language,
            "supported_languages": self.SUPPORTED_LANGUAGES,
        }


_lang_manager: Optional[LanguageManager] = None


def get_language_manager() -> LanguageManager:
    global _lang_manager
    if _lang_manager is None:
        _lang_manager = LanguageManager()
    return _lang_manager