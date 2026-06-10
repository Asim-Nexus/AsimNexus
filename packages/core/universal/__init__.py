"""
core/universal/__init__.py
AsimNexus — Universal Systems stub module.

Provides stub implementations for currency, legal, timezone, and i18n systems.
These are placeholders for future real implementations.
"""

from enum import Enum
from typing import Any, Dict, List, Optional


# ─── Currency System ───────────────────────────────────────────────────────────

class CurrencyType(Enum):
    FIAT = "fiat"
    CRYPTO = "crypto"


class Currency:
    """Stub currency data class."""
    def __init__(self, code: str, name: str, symbol: str, currency_type: str = "fiat", decimals: int = 2):
        self.code = code
        self.name = name
        self.symbol = symbol
        self.type = CurrencyType.FIAT if currency_type == "fiat" else CurrencyType.CRYPTO
        self.decimals = decimals

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "symbol": self.symbol,
            "type": self.type.value,
            "decimals": self.decimals,
        }


_STUB_CURRENCIES = [
    Currency("USD", "US Dollar", "$", "fiat"),
    Currency("EUR", "Euro", "€", "fiat"),
    Currency("GBP", "British Pound", "£", "fiat"),
    Currency("JPY", "Japanese Yen", "¥", "fiat"),
    Currency("NPR", "Nepalese Rupee", "रू", "fiat"),
    Currency("BTC", "Bitcoin", "₿", "crypto"),
    Currency("ETH", "Ethereum", "Ξ", "crypto"),
]

_STUB_CURRENCIES_BY_COUNTRY: Dict[str, List[Currency]] = {
    "US": [Currency("USD", "US Dollar", "$")],
    "NP": [Currency("NPR", "Nepalese Rupee", "रू")],
    "GB": [Currency("GBP", "British Pound", "£")],
    "EU": [Currency("EUR", "Euro", "€")],
    "JP": [Currency("JPY", "Japanese Yen", "¥")],
}


class CurrencySystem:
    """Stub currency system."""

    def get_stats(self) -> Dict[str, Any]:
        fiat_count = sum(1 for c in _STUB_CURRENCIES if c.type == CurrencyType.FIAT)
        crypto_count = sum(1 for c in _STUB_CURRENCIES if c.type == CurrencyType.CRYPTO)
        return {
            "total_currencies": len(_STUB_CURRENCIES),
            "fiat_currencies": fiat_count,
            "crypto_currencies": crypto_count,
            "countries_covered": len(_STUB_CURRENCIES_BY_COUNTRY),
        }

    def get_all_currencies(self) -> List[Currency]:
        return _STUB_CURRENCIES

    def get_currencies_by_country(self, country_code: str) -> List[Currency]:
        return _STUB_CURRENCIES_BY_COUNTRY.get(country_code.upper(), [])

    async def fetch_exchange_rates(self) -> None:
        pass

    def convert(self, amount, from_currency: str, to_currency: str):
        """Simple stub conversion — return amount unchanged for same currency."""
        if from_currency == to_currency:
            return amount
        # Stub: approximate conversion rates
        rates = {
            ("USD", "EUR"): 0.92,
            ("EUR", "USD"): 1.09,
            ("USD", "GBP"): 0.79,
            ("GBP", "USD"): 1.27,
            ("USD", "NPR"): 133.50,
            ("NPR", "USD"): 0.0075,
        }
        rate = rates.get((from_currency, to_currency))
        if rate is None:
            return None
        return amount * rate

    def format_amount(self, amount, currency: str) -> str:
        symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "NPR": "रू", "BTC": "₿", "ETH": "Ξ"}
        sym = symbols.get(currency, currency)
        return f"{sym}{amount:.2f}"


# ─── Legal / Country System ────────────────────────────────────────────────────

class DataResidency(Enum):
    LOCAL = "local"
    REGIONAL = "regional"
    CLOUD = "cloud"
    GLOBAL = "global"


class CryptoReg(Enum):
    FRIENDLY = "friendly"
    RESTRICTIVE = "restrictive"
    BANNED = "banned"
    NEUTRAL = "neutral"


class Country:
    """Stub country data class."""
    def __init__(self, code: str, name: str, region: str = "asia",
                 privacy_laws: str = "basic", data_residency: str = "cloud",
                 gdpr_compatible: bool = False, crypto_reg: str = "neutral",
                 dharma_compatible: bool = False, tax_authority: str = "",
                 vat_rate: float = 0.0, right_to_be_forgotten: bool = False,
                 notes: str = ""):
        self.code = code
        self.name = name
        self.region = region
        self.privacy_laws = privacy_laws
        self.data_residency = DataResidency(data_residency)
        self.gdpr_compatible = gdpr_compatible
        self.crypto_reg = CryptoReg(crypto_reg)
        self.dharma_compatible = dharma_compatible
        self.tax_authority = tax_authority
        self.vat_rate = vat_rate
        self.right_to_be_forgotten = right_to_be_forgotten
        self.notes = notes


_STUB_COUNTRIES = [
    Country("US", "United States", "north_america", "sectoral", "cloud",
            False, "friendly", False, "IRS", 0.0, False, "Federal system"),
    Country("NP", "Nepal", "asia", "basic", "local",
            False, "neutral", True, "IRD", 13.0, True, "Dharma-compatible"),
    Country("GB", "United Kingdom", "europe", "uk_gdpr", "regional",
            True, "friendly", False, "HMRC", 20.0, True, "Post-Brexit regime"),
    Country("DE", "Germany", "europe", "gdpr", "regional",
            True, "restrictive", False, "Finanzamt", 19.0, True, "GDPR strict"),
    Country("EE", "Estonia", "europe", "gdpr", "cloud",
            True, "friendly", False, "MTA", 20.0, True, "e-Residency pioneer"),
    Country("JP", "Japan", "asia", "appi", "local",
            False, "friendly", False, "NTA", 10.0, False, "APPI framework"),
]


class LegalFramework:
    """Stub legal framework / country system."""

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_countries": len(_STUB_COUNTRIES),
            "gdpr_compliant": sum(1 for c in _STUB_COUNTRIES if c.gdpr_compatible),
            "dharma_compatible": sum(1 for c in _STUB_COUNTRIES if c.dharma_compatible),
            "crypto_friendly": sum(1 for c in _STUB_COUNTRIES if c.crypto_reg == CryptoReg.FRIENDLY),
        }

    def get_all(self) -> List[Country]:
        return _STUB_COUNTRIES

    def get_country(self, code: str) -> Optional[Country]:
        for c in _STUB_COUNTRIES:
            if c.code.upper() == code.upper():
                return c
        return None


# ─── Timezone System ───────────────────────────────────────────────────────────

class TimezoneInfo:
    """Stub timezone info."""
    def __init__(self, code: str, name: str, offset: str, dst: bool = False,
                 major_cities: Optional[List[str]] = None):
        self.code = code
        self.name = name
        self.offset = offset
        self.dst = dst
        self.major_cities = major_cities or []


_STUB_TIMEZONES = {
    "America/New_York": TimezoneInfo("America/New_York", "Eastern Time", "-05:00", True, ["New York", "Washington DC"]),
    "America/Los_Angeles": TimezoneInfo("America/Los_Angeles", "Pacific Time", "-08:00", True, ["Los Angeles", "San Francisco"]),
    "Europe/London": TimezoneInfo("Europe/London", "Greenwich Mean Time", "+00:00", True, ["London"]),
    "Europe/Berlin": TimezoneInfo("Europe/Berlin", "Central European Time", "+01:00", True, ["Berlin", "Paris"]),
    "Asia/Kathmandu": TimezoneInfo("Asia/Kathmandu", "Nepal Time", "+05:45", False, ["Kathmandu"]),
    "Asia/Tokyo": TimezoneInfo("Asia/Tokyo", "Japan Standard Time", "+09:00", False, ["Tokyo"]),
}

_STUB_TIMEZONES_BY_COUNTRY: Dict[str, List[str]] = {
    "US": ["America/New_York", "America/Los_Angeles"],
    "NP": ["Asia/Kathmandu"],
    "GB": ["Europe/London"],
    "DE": ["Europe/Berlin"],
    "JP": ["Asia/Tokyo"],
}


class TimezoneSystem:
    """Stub timezone system."""

    TIME_ZONES = _STUB_TIMEZONES

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_timezones": len(_STUB_TIMEZONES),
            "countries_covered": len(_STUB_TIMEZONES_BY_COUNTRY),
        }

    def get_for_country(self, country_code: str) -> List[TimezoneInfo]:
        codes = _STUB_TIMEZONES_BY_COUNTRY.get(country_code.upper(), [])
        return [_STUB_TIMEZONES[c] for c in codes if c in _STUB_TIMEZONES]


# ─── i18n System ───────────────────────────────────────────────────────────────

class LanguageTier(Enum):
    TIER1 = "tier1"
    TIER2 = "tier2"


class Language:
    """Stub language data class."""
    def __init__(self, code: str, name: str, native_name: str,
                 speakers_millions: float = 0, tier: str = "tier2",
                 rtl: bool = False, script: str = "Latin",
                 countries: Optional[List[str]] = None):
        self.code = code
        self.name = name
        self.native_name = native_name
        self.speakers_millions = speakers_millions
        self.tier = LanguageTier.TIER1 if tier == "tier1" else LanguageTier.TIER2
        self.rtl = rtl
        self.script = script
        self.countries = countries or []


_STUB_LANGUAGES = [
    Language("en", "English", "English", 1500, "tier1", False, "Latin", ["US", "GB"]),
    Language("ne", "Nepali", "नेपाली", 30, "tier2", False, "Devanagari", ["NP"]),
    Language("de", "German", "Deutsch", 130, "tier1", False, "Latin", ["DE"]),
    Language("ja", "Japanese", "日本語", 125, "tier2", False, "Kana", ["JP"]),
    Language("ar", "Arabic", "العربية", 420, "tier2", True, "Arabic", []),
    Language("es", "Spanish", "Español", 600, "tier1", False, "Latin", []),
]


class I18nSystem:
    """Stub i18n / language system."""

    def get_stats(self) -> Dict[str, Any]:
        tier1 = sum(1 for l in _STUB_LANGUAGES if l.tier == LanguageTier.TIER1)
        tier2 = sum(1 for l in _STUB_LANGUAGES if l.tier == LanguageTier.TIER2)
        rtl = sum(1 for l in _STUB_LANGUAGES if l.rtl)
        total_speakers = sum(l.speakers_millions for l in _STUB_LANGUAGES)
        return {
            "tier1_languages": tier1,
            "tier2_languages": tier2,
            "total_languages": len(_STUB_LANGUAGES),
            "estimated_speakers_billions": round(total_speakers / 1000, 1),
            "rtl_languages": rtl,
        }

    def get_all_languages(self) -> List[Language]:
        return _STUB_LANGUAGES

    def get_language(self, code: str) -> Optional[Language]:
        for lang in _STUB_LANGUAGES:
            if lang.code.lower() == code.lower():
                return lang
        return None

    def translate(self, key: str, lang_code: str) -> str:
        """Stub translation — return key as-is."""
        return key


# ─── Singleton Accessors ───────────────────────────────────────────────────────

_CURRENCY_SYSTEM: Optional[CurrencySystem] = None
_LEGAL_FRAMEWORK: Optional[LegalFramework] = None
_TIMEZONE_SYSTEM: Optional[TimezoneSystem] = None
_I18N_SYSTEM: Optional[I18nSystem] = None


def get_currency_system() -> CurrencySystem:
    global _CURRENCY_SYSTEM
    if _CURRENCY_SYSTEM is None:
        _CURRENCY_SYSTEM = CurrencySystem()
    return _CURRENCY_SYSTEM


def get_legal_framework() -> LegalFramework:
    global _LEGAL_FRAMEWORK
    if _LEGAL_FRAMEWORK is None:
        _LEGAL_FRAMEWORK = LegalFramework()
    return _LEGAL_FRAMEWORK


def get_timezone_system() -> TimezoneSystem:
    global _TIMEZONE_SYSTEM
    if _TIMEZONE_SYSTEM is None:
        _TIMEZONE_SYSTEM = TimezoneSystem()
    return _TIMEZONE_SYSTEM


def get_i18n_system() -> I18nSystem:
    global _I18N_SYSTEM
    if _I18N_SYSTEM is None:
        _I18N_SYSTEM = I18nSystem()
    return _I18N_SYSTEM


__all__ = [
    "CurrencySystem", "Currency", "CurrencyType",
    "LegalFramework", "Country", "DataResidency", "CryptoReg",
    "TimezoneSystem", "TimezoneInfo",
    "I18nSystem", "Language", "LanguageTier",
    "get_currency_system", "get_legal_framework",
    "get_timezone_system", "get_i18n_system",
]
