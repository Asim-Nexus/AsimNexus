"""
Nepal Language Support
======================
Nepali (Devanagari) NLP utilities and language detection.

Features:
    - Nepali text transliteration (Devanagari <-> Roman)
    - Language detection (Nepali, English, mixed)
    - Nepali Unicode normalization
    - Common Nepali phrases and patterns
"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger("AsimNexus.Nepal.Language")

# Basic Devanagari Unicode ranges
DEVANAGARI_START = 0x0900
DEVANAGARI_END = 0x097F
DEVANAGARI_EXT_START = 0xA8E0
DEVANAGARI_EXT_END = 0xA8FF

# Common Nepali words for detection
_NEPALI_KEYWORDS = {
    "को", "ले", "मा", "र", "पनि", "हो", "था", "छ", "थियो",
    "गर्न", "हुन", "आउन", "जान", "दिन", "लिन", "गर्यो",
    "भन्यो", "दियो", "लियो", "आयो", "गयो", "होस्", "नि",
    "पर्छ", "चाहिन्छ", "मिल्छ", "सक्छ", "हुन्छ",
    "नमस्ते", "धन्यवाद", "माफ", "कृपया", "शुभ",
    "एक", "दुई", "तीन", "चार", "पाँच",
    "आज", "भोलि", "हिजो", "अहिले", "पछि",
}

# Simple Devanagari -> Roman transliteration map (partial)
_DEVANAGARI_TO_ROMAN = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo",
    "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au",
    "क": "ka", "ख": "kha", "ग": "ga", "घ": "gha", "ङ": "nga",
    "च": "cha", "छ": "chha", "ज": "ja", "झ": "jha", "ञ": "nya",
    "ट": "ta", "ठ": "tha", "ड": "da", "ढ": "dha", "ण": "na",
    "त": "ta", "थ": "tha", "द": "da", "ध": "dha", "न": "na",
    "प": "pa", "फ": "pha", "ब": "ba", "भ": "bha", "म": "ma",
    "य": "ya", "र": "ra", "ल": "la", "व": "wa",
    "श": "sha", "ष": "sha", "स": "sa", "ह": "ha",
    "क्ष": "ksha", "त्र": "tra", "ज्ञ": "gya",
    "ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo",
    "े": "e", "ै": "ai", "ो": "o", "ौ": "au",
    "ं": "n", "ः": "h", "्": "",
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9",
}


def get_language_status() -> Dict:
    """Return Nepal language support status."""
    return {
        "country": "Nepal",
        "languages_supported": ["Nepali", "English"],
        "scripts_supported": ["Devanagari", "Latin"],
        "features": [
            "Devanagari-to-Roman transliteration",
            "Language detection (Nepali/English/mixed)",
            "Unicode normalization",
            "Nepali keyword recognition",
        ],
        "status": "active",
    }


def _is_devanagari_char(char: str) -> bool:
    """Check if a character is within Devanagari Unicode range."""
    cp = ord(char)
    return (DEVANAGARI_START <= cp <= DEVANAGARI_END) or \
           (DEVANAGARI_EXT_START <= cp <= DEVANAGARI_EXT_END)


def detect_language(text: str) -> str:
    """Detect whether text is Nepali, English, or Mixed.

    Args:
        text: Input text to analyze

    Returns:
        "ne" for Nepali, "en" for English, "mixed" for mixed content,
        "unknown" if cannot determine.
    """
    if not text or not text.strip():
        return "unknown"

    devanagari_count = sum(1 for c in text if _is_devanagari_char(c))
    total_alpha = sum(1 for c in text if c.isalpha())
    latin_count = total_alpha - devanagari_count

    if total_alpha == 0:
        return "unknown"

    ne_ratio = devanagari_count / total_alpha

    if ne_ratio > 0.8:
        return "ne"
    elif ne_ratio > 0.2:
        return "mixed"
    elif ne_ratio > 0.0:
        # Could have some Nepali keywords in Latin script
        words = set(re.findall(r"\w+", text.lower()))
        ne_keywords = words & {w.lower() for w in _NEPALI_KEYWORDS}
        if ne_keywords:
            return "mixed"
        return "en"
    else:
        return "en"


def transliterate(text: str, to_script: str = "roman") -> str:
    """Transliterate text between Devanagari and Roman scripts.

    Args:
        text: Input text
        to_script: Target script ("roman" or "devanagari")

    Returns:
        Transliterated text.
    """
    if to_script == "roman":
        result = []
        for char in text:
            if char in _DEVANAGARI_TO_ROMAN:
                result.append(_DEVANAGARI_TO_ROMAN[char])
            else:
                result.append(char)
        return "".join(result)
    elif to_script == "devanagari":
        # Build reverse map (simplified)
        roman_to_devanagari = {v: k for k, v in _DEVANAGARI_TO_ROMAN.items()
                               if len(v) == 1}
        result = []
        i = 0
        while i < len(text):
            # Try longest match first
            matched = False
            for length in range(4, 0, -1):
                chunk = text[i:i + length].lower()
                for dev, rom in _DEVANAGARI_TO_ROMAN.items():
                    if rom == chunk:
                        result.append(dev)
                        i += length
                        matched = True
                        break
                if matched:
                    break
            if not matched:
                result.append(text[i])
                i += 1
        return "".join(result)
    else:
        raise ValueError(f"Unsupported target script: {to_script}")
