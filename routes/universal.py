"""
AsimNexus Universal Route Module
=================================
Universal data (countries, currencies, languages, timezones),
lifecycle management, personal OS, and universe operations.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Body
from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.Universal")

router = APIRouter(tags=["Universal"])

# Module-level globals (set via init_universal)
orchestrator = None


def init_universal(app_globals: dict) -> None:
    """Initialize universal router with shared application globals."""
    global orchestrator
    orchestrator = app_globals.get("orchestrator")


# ──────────────────────────────────────────────
#  Universal Data Endpoints
# ──────────────────────────────────────────────


@router.get("/api/universal/status")
async def universal_status():
    """Get universal system status."""
    try:
        return ok(data={"status": "active", "universal_system": "available"})
    except Exception as e:
        return error(str(e))


@router.get("/api/universal/countries")
async def universal_countries():
    """Get all supported countries."""
    try:
        from core.universal import get_legal_framework
        lf = get_legal_framework()
        countries = lf.get_all_countries()
        return ok(data={
            "total": len(countries),
            "countries": [{"code": c.code, "name": c.name, "region": c.region} for c in countries]
        })
    except Exception as e:
        return error(str(e))


@router.get("/api/universal/currencies")
async def universal_currencies():
    """Get all supported currencies."""
    try:
        from core.universal import get_currency_system
        cs = get_currency_system()
        currencies = cs.get_all_currencies()
        return ok(data={
            "total": len(currencies),
            "currencies": [{"code": c.code, "name": c.name, "symbol": c.symbol} for c in currencies]
        })
    except Exception as e:
        return error(str(e))


@router.get("/api/universal/languages")
async def universal_languages():
    """Get all supported languages."""
    try:
        from core.universal import get_i18n_system
        i18n = get_i18n_system()
        languages = i18n.get_all_languages()
        return ok(data={
            "total": len(languages),
            "languages": [{"code": l.code, "name": l.name, "native_name": l.native_name} for l in languages]
        })
    except Exception as e:
        return error(str(e))


@router.get("/api/universal/timezones")
async def universal_timezones():
    """Get all supported timezones."""
    try:
        from core.universal import get_timezone_system
        tz = get_timezone_system()
        timezones = tz.get_all_timezones()
        return ok(data={
            "total": len(timezones),
            "timezones": [{"code": t.code, "name": t.name, "offset": t.offset} for t in timezones]
        })
    except Exception as e:
        return error(str(e))


@router.get("/api/universal/currencies/{country_code}")
async def universal_currencies_for_country(country_code: str):
    """Get currencies for a specific country"""
    try:
        from core.universal import get_currency_system
        cs = get_currency_system()
        currencies = cs.get_currencies_by_country(country_code)
        return ok(data={
            "country": country_code.upper(),
            "currencies": [c.to_dict() for c in currencies],
            "count": len(currencies)
        })
    except Exception as e:
        return error(str(e))


@router.post("/api/universal/currency/convert")
async def universal_currency_convert(data: dict = Body(...)):
    """Convert between currencies"""
    try:
        from core.universal import get_currency_system
        from decimal import Decimal

        amount = data.get('amount', 0)
        from_currency = data.get('from', 'USD')
        to_currency = data.get('to', 'USD')

        cs = get_currency_system()

        # Fetch rates if needed
        await cs.fetch_exchange_rates()

        result = cs.convert(Decimal(str(amount)), from_currency, to_currency)

        if result is None:
            return error(f"Could not convert from {from_currency} to {to_currency}")

        return ok(data={
            "amount": float(amount),
            "from": from_currency,
            "to": to_currency,
            "result": float(result),
            "formatted": cs.format_amount(result, to_currency),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return error(str(e))


@router.get("/api/universal/countries/{country_code}")
async def universal_country_detail(country_code: str):
    """Get detailed info for a country"""
    try:
        from core.universal import get_legal_framework, get_currency_system
        from core.universal import get_timezone_system

        lf = get_legal_framework()
        country = lf.get_country(country_code)

        if not country:
            return error(f"Country {country_code} not found")

        cs = get_currency_system()
        currencies = cs.get_currencies_by_country(country_code)

        tz = get_timezone_system()
        timezones = tz.get_for_country(country_code)

        return ok(data={
            "code": country.code,
            "name": country.name,
            "region": country.region,
            "privacy_laws": country.privacy_laws,
            "data_residency": country.data_residency.value,
            "gdpr_compatible": country.gdpr_compatible,
            "right_to_be_forgotten": country.right_to_be_forgotten,
            "crypto_regulation": country.crypto_reg.value,
            "tax_authority": country.tax_authority,
            "vat_rate": country.vat_rate,
            "dharma_compatible": country.dharma_compatible,
            "notes": country.notes,
            "currencies": [c.code for c in currencies],
            "timezones": [t.code for t in timezones],
        })
    except Exception as e:
        return error(str(e))


@router.get("/api/universal/languages/{lang_code}")
async def universal_language_detail(lang_code: str):
    """Get language details"""
    try:
        from core.universal import get_i18n_system
        i18n = get_i18n_system()

        lang = i18n.get_language(lang_code)
        if not lang:
            return error(f"Language {lang_code} not found")

        # Test translation
        test_keys = ['welcome', 'login', 'dashboard', 'dharma']
        translations = {key: i18n.translate(key, lang_code) for key in test_keys}

        return ok(data={
            "code": lang.code,
            "name": lang.name,
            "native_name": lang.native_name,
            "speakers_millions": lang.speakers_millions,
            "tier": lang.tier.value,
            "rtl": lang.rtl,
            "script": lang.script,
            "countries": lang.countries,
            "sample_translations": translations,
        })
    except Exception as e:
        return error(str(e))


@router.get("/api/universal/timezones/{country_code}")
async def universal_timezones_for_country(country_code: str):
    """Get timezones for a country"""
    try:
        from core.universal import get_timezone_system
        tz = get_timezone_system()

        timezones = tz.get_for_country(country_code)
        current_times = {}

        for t in timezones:
            now = tz.get_current_time(t.code)
            if now:
                current_times[t.code] = now.strftime('%Y-%m-%d %H:%M:%S %Z')

        return ok(data={
            "country": country_code.upper(),
            "timezones": [{"code": t.code, "name": t.name, "offset": t.offset}
                          for t in timezones],
            "current_times": current_times,
        })
    except Exception as e:
        return error(str(e))


@router.get("/api/universal/meeting-times")
async def universal_meeting_times(timezones: str):
    """Get best meeting times for given timezones"""
    try:
        from core.universal import get_timezone_system
        tz = get_timezone_system()

        tz_list = [t.strip() for t in timezones.split(',')]
        best_times = tz.get_best_meeting_time(tz_list)

        return ok(data={
            "participants": tz_list,
            "best_times": best_times[:5]  # Top 5
        })
    except Exception as e:
        return error(str(e))


# ──────────────────────────────────────────────
#  Lifecycle Endpoints
# ──────────────────────────────────────────────


@router.get("/api/universe/{user_id}/lifecycle")
async def universe_lifecycle(user_id: str):
    """Get user universe lifecycle."""
    try:
        from core.life_journey import get_life_journey
        lj = get_life_journey()
        return ok(data=lj.get_lifecycle(user_id))
    except Exception as e:
        return error(str(e))


@router.get("/api/universe/{user_id}/status")
async def universe_user_status(user_id: str):
    """Get user universe status."""
    try:
        from core.universe.personal_universe import get_universe_manager
        manager = get_universe_manager()
        universe = manager.get_universe(user_id)
        if not universe:
            return error("Universe not found")
        return ok(data={
            "user_id": universe.user_id,
            "state": universe.state.value,
            "created_at": universe.created_at.isoformat() if hasattr(universe, 'created_at') else None,
        })
    except Exception as e:
        return error(str(e))


@router.post("/api/universe/{user_id}/layer/activate")
async def universe_activate_layer(user_id: str, data: dict = Body(...)):
    """Activate a layer in user universe."""
    try:
        from core.universe.personal_universe import get_universe_manager
        manager = get_universe_manager()
        layer = data.get("layer", "base")
        result = manager.activate_layer(user_id, layer)
        return ok(data={"success": result, "layer": layer})
    except Exception as e:
        return error(str(e))


@router.get("/api/universe/stats")
async def universe_stats():
    """Get universe statistics."""
    try:
        from core.universe.personal_universe import get_universe_manager
        manager = get_universe_manager()
        return ok(data=manager.get_stats())
    except Exception as e:
        return error(str(e))


@router.post("/api/universe/{user_id}/archive")
async def archive_universe(user_id: str, data: dict = Body(...)):
    """Archive user universe"""
    try:
        from core.universe.personal_universe import get_universe_manager

        manager = get_universe_manager()
        success = manager.archive_universe(
            user_id=user_id,
            reason=data.get("reason", "User request")
        )

        return ok(data={
            "success": success,
            "message": "Universe archived" if success else "Failed to archive"
        })
    except Exception as e:
        logger.error(f"Archive error: {e}")
        return error(str(e))


@router.post("/api/universe/{user_id}/reactivate")
async def reactivate_universe(user_id: str):
    """Reactivate archived universe"""
    try:
        from core.universe.personal_universe import get_universe_manager

        manager = get_universe_manager()
        success = manager.reactivate_universe(user_id=user_id)

        return ok(data={
            "success": success,
            "message": "Universe reactivated" if success else "Failed to reactivate"
        })
    except Exception as e:
        logger.error(f"Reactivate error: {e}")
        return error(str(e))


@router.post("/api/universe/create")
async def api_create_universe(data: dict = Body(...)):
    """Create new universe"""
    try:
        from core.universe.personal_universe import get_universe_manager

        manager = get_universe_manager()

        universe = manager.create_universe(
            user_id=data.get("user_id"),
            email=data.get("email"),
            display_name=data.get("display_name", "Anonymous")
        )

        return ok(data={
            "success": True,
            "universe_id": universe.user_id,
            "state": universe.state.value
        })
    except Exception as e:
        logger.error(f"Universe create error: {e}")
        return error(str(e))
