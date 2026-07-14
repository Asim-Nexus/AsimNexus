"""
DePIN Connectors API — Decentralized Physical Infrastructure Network endpoints.
================================================================================
Exposes Uplink (decentralized internet), Daylight (decentralized energy),
and DIMO (connected vehicles) connectors via REST API.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Body, Query

from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.DePIN")

router = APIRouter(tags=["DePIN"])

# ── Singletons ───────────────────────────────────────────────────────────────

_uplink = None
_daylight = None
_dimo = None


def init_depin(app_globals: dict) -> None:
    """Initialize DePIN connectors with shared state."""
    global _uplink, _daylight, _dimo
    try:
        from core.depin.uplink_connector import UplinkConnector
        _uplink = UplinkConnector()
        logger.info("UplinkConnector instance created")
    except Exception as e:
        logger.warning(f"UplinkConnector not available: {e}")

    try:
        from core.depin.daylight_connector import DaylightConnector
        _daylight = DaylightConnector()
        logger.info("DaylightConnector instance created")
    except Exception as e:
        logger.warning(f"DaylightConnector not available: {e}")

    try:
        from core.depin.dimo_connector import DIMOConnector
        _dimo = DIMOConnector()
        logger.info("DIMOConnector instance created")
    except Exception as e:
        logger.warning(f"DIMOConnector not available: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# UPLINK — Decentralized Internet Connectivity
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/depin/uplink/connect")
async def depin_uplink_connect():
    """Connect to the Uplink decentralized wireless network."""
    try:
        if not _uplink:
            return error("Uplink connector not available")
        result = await _uplink.connect()
        return ok(data={"connected": result})
    except Exception as e:
        logger.error(f"depin_uplink_connect error: {e}")
        return error(str(e))


@router.post("/api/depin/uplink/disconnect")
async def depin_uplink_disconnect():
    """Disconnect from the Uplink network."""
    try:
        if not _uplink:
            return error("Uplink connector not available")
        result = await _uplink.disconnect()
        return ok(data={"disconnected": result})
    except Exception as e:
        logger.error(f"depin_uplink_disconnect error: {e}")
        return error(str(e))


@router.post("/api/depin/uplink/nodes")
async def depin_uplink_register_node(data: dict = Body(...)):
    """Register a new node in the Uplink network."""
    try:
        if not _uplink:
            return error("Uplink connector not available")
        node = await _uplink.register_node(
            node_id=data.get("node_id", ""),
            address=data.get("address", ""),
            bandwidth_capacity=data.get("bandwidth_capacity", 100.0),
            location=data.get("location", ""),
        )
        return ok(data={
            "id": node.id,
            "address": node.address,
            "bandwidth_capacity": node.bandwidth_capacity,
            "state": node.state.value,
            "location": node.location,
        })
    except Exception as e:
        logger.error(f"depin_uplink_register_node error: {e}")
        return error(str(e))


@router.post("/api/depin/uplink/nodes/{node_id}/offload")
async def depin_uplink_offload(node_id: str, data: dict = Body(...)):
    """Offload traffic to an Uplink node."""
    try:
        if not _uplink:
            return error("Uplink connector not available")
        amount = data.get("amount_mbps", 0.0)
        result = await _uplink.offload_traffic(node_id, amount)
        return ok(data={"success": result, "node_id": node_id, "amount_mbps": amount})
    except Exception as e:
        logger.error(f"depin_uplink_offload error: {e}")
        return error(str(e))


@router.post("/api/depin/uplink/nodes/{node_id}/release")
async def depin_uplink_release(node_id: str, data: dict = Body(...)):
    """Release traffic from an Uplink node."""
    try:
        if not _uplink:
            return error("Uplink connector not available")
        amount = data.get("amount_mbps", 0.0)
        result = await _uplink.release_traffic(node_id, amount)
        return ok(data={"success": result, "node_id": node_id, "amount_mbps": amount})
    except Exception as e:
        logger.error(f"depin_uplink_release error: {e}")
        return error(str(e))


@router.post("/api/depin/uplink/nodes/{node_id}/rewards")
async def depin_uplink_claim_rewards(node_id: str):
    """Claim accumulated rewards for an Uplink node."""
    try:
        if not _uplink:
            return error("Uplink connector not available")
        reward = await _uplink.claim_rewards(node_id)
        return ok(data={"node_id": node_id, "reward": reward})
    except Exception as e:
        logger.error(f"depin_uplink_claim_rewards error: {e}")
        return error(str(e))


@router.get("/api/depin/uplink/stats")
async def depin_uplink_stats():
    """Get Uplink network statistics."""
    try:
        if not _uplink:
            return error("Uplink connector not available")
        stats = _uplink.get_network_stats()
        return ok(data=stats)
    except Exception as e:
        logger.error(f"depin_uplink_stats error: {e}")
        return error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# DAYLIGHT — Decentralized Energy Distribution
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/depin/daylight/connect")
async def depin_daylight_connect():
    """Connect to the Daylight decentralized energy network."""
    try:
        if not _daylight:
            return error("Daylight connector not available")
        result = await _daylight.connect()
        return ok(data={"connected": result})
    except Exception as e:
        logger.error(f"depin_daylight_connect error: {e}")
        return error(str(e))


@router.post("/api/depin/daylight/disconnect")
async def depin_daylight_disconnect():
    """Disconnect from the Daylight network."""
    try:
        if not _daylight:
            return error("Daylight connector not available")
        result = await _daylight.disconnect()
        return ok(data={"disconnected": result})
    except Exception as e:
        logger.error(f"depin_daylight_disconnect error: {e}")
        return error(str(e))


@router.post("/api/depin/daylight/devices")
async def depin_daylight_register_device(data: dict = Body(...)):
    """Register a new energy device in the Daylight network."""
    try:
        if not _daylight:
            return error("Daylight connector not available")
        from core.depin.daylight_connector import DeviceType
        dt_str = data.get("device_type", "solar_inverter")
        device_type = DeviceType(dt_str)
        device = await _daylight.register_device(
            device_id=data.get("device_id", ""),
            device_type=device_type,
            capacity_kwh=data.get("capacity_kwh", 10.0),
            location=data.get("location", ""),
        )
        return ok(data={
            "id": device.id,
            "device_type": device.device_type.value,
            "capacity_kwh": device.capacity_kwh,
            "state": device.state.value,
            "location": device.location,
        })
    except Exception as e:
        logger.error(f"depin_daylight_register_device error: {e}")
        return error(str(e))


@router.put("/api/depin/daylight/devices/{device_id}/output")
async def depin_daylight_update_output(device_id: str, data: dict = Body(...)):
    """Update the energy output of a device."""
    try:
        if not _daylight:
            return error("Daylight connector not available")
        from core.depin.daylight_connector import EnergyState
        output_kwh = data.get("output_kwh", 0.0)
        state_str = data.get("state", "idle")
        state = EnergyState(state_str)
        result = await _daylight.update_energy_output(device_id, output_kwh, state)
        return ok(data={"success": result, "device_id": device_id, "output_kwh": output_kwh, "state": state.value})
    except Exception as e:
        logger.error(f"depin_daylight_update_output error: {e}")
        return error(str(e))


@router.post("/api/depin/daylight/devices/{device_id}/sell")
async def depin_daylight_sell_energy(device_id: str, data: dict = Body(...)):
    """Sell energy from a device to the grid."""
    try:
        if not _daylight:
            return error("Daylight connector not available")
        amount_kwh = data.get("amount_kwh", 0.0)
        price_per_kwh = data.get("price_per_kwh", 0.0)
        result = await _daylight.sell_energy(device_id, amount_kwh, price_per_kwh)
        return ok(data=result)
    except Exception as e:
        logger.error(f"depin_daylight_sell_energy error: {e}")
        return error(str(e))


@router.post("/api/depin/daylight/buy")
async def depin_daylight_buy_energy(data: dict = Body(...)):
    """Buy energy from the grid."""
    try:
        if not _daylight:
            return error("Daylight connector not available")
        amount_kwh = data.get("amount_kwh", 0.0)
        max_price = data.get("max_price_per_kwh", 0.0)
        result = await _daylight.buy_energy(amount_kwh, max_price)
        return ok(data=result)
    except Exception as e:
        logger.error(f"depin_daylight_buy_energy error: {e}")
        return error(str(e))


@router.post("/api/depin/daylight/devices/{device_id}/carbon-credits")
async def depin_daylight_claim_carbon_credits(device_id: str):
    """Claim carbon credits for a device."""
    try:
        if not _daylight:
            return error("Daylight connector not available")
        credits = await _daylight.claim_carbon_credits(device_id)
        return ok(data={"device_id": device_id, "carbon_credits": credits})
    except Exception as e:
        logger.error(f"depin_daylight_claim_carbon_credits error: {e}")
        return error(str(e))


@router.get("/api/depin/daylight/stats")
async def depin_daylight_stats():
    """Get Daylight network statistics."""
    try:
        if not _daylight:
            return error("Daylight connector not available")
        stats = _daylight.get_network_stats()
        return ok(data=stats)
    except Exception as e:
        logger.error(f"depin_daylight_stats error: {e}")
        return error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# DIMO — Connected Vehicles and IoT
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/depin/dimo/connect")
async def depin_dimo_connect():
    """Connect to the DIMO decentralized vehicle network."""
    try:
        if not _dimo:
            return error("DIMO connector not available")
        result = await _dimo.connect()
        return ok(data={"connected": result})
    except Exception as e:
        logger.error(f"depin_dimo_connect error: {e}")
        return error(str(e))


@router.post("/api/depin/dimo/disconnect")
async def depin_dimo_disconnect():
    """Disconnect from the DIMO network."""
    try:
        if not _dimo:
            return error("DIMO connector not available")
        result = await _dimo.disconnect()
        return ok(data={"disconnected": result})
    except Exception as e:
        logger.error(f"depin_dimo_disconnect error: {e}")
        return error(str(e))


@router.post("/api/depin/dimo/vehicles")
async def depin_dimo_register_vehicle(data: dict = Body(...)):
    """Register a new vehicle in the DIMO network."""
    try:
        if not _dimo:
            return error("DIMO connector not available")
        vehicle = await _dimo.register_vehicle(
            vehicle_id=data.get("vehicle_id", ""),
            vin=data.get("vin", ""),
            make=data.get("make", ""),
            model=data.get("model", ""),
            year=data.get("year", 2024),
        )
        return ok(data={
            "id": vehicle.id,
            "vin": vehicle.vin,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "state": vehicle.state.value,
        })
    except Exception as e:
        logger.error(f"depin_dimo_register_vehicle error: {e}")
        return error(str(e))


@router.put("/api/depin/dimo/vehicles/{vehicle_id}/telemetry")
async def depin_dimo_update_telemetry(vehicle_id: str, data: dict = Body(...)):
    """Update vehicle telemetry data."""
    try:
        if not _dimo:
            return error("DIMO connector not available")
        from core.depin.dimo_connector import DataType
        dt_str = data.get("data_type", "speed")
        data_type = DataType(dt_str)
        value = data.get("value", 0.0)
        result = await _dimo.update_telemetry(vehicle_id, data_type, value)
        return ok(data={"success": result, "vehicle_id": vehicle_id, "data_type": dt_str, "value": value})
    except Exception as e:
        logger.error(f"depin_dimo_update_telemetry error: {e}")
        return error(str(e))


@router.post("/api/depin/dimo/vehicles/{vehicle_id}/share")
async def depin_dimo_share_data(vehicle_id: str, data: dict = Body(...)):
    """Share vehicle data with the network."""
    try:
        if not _dimo:
            return error("DIMO connector not available")
        from core.depin.dimo_connector import DataType
        data_types_str = data.get("data_types", ["speed"])
        data_types = [DataType(dt) for dt in data_types_str]
        duration = data.get("duration_minutes", 60)
        result = await _dimo.share_data(vehicle_id, data_types, duration)
        return ok(data=result)
    except Exception as e:
        logger.error(f"depin_dimo_share_data error: {e}")
        return error(str(e))


@router.post("/api/depin/dimo/vehicles/{vehicle_id}/permissions")
async def depin_dimo_grant_permission(vehicle_id: str, data: dict = Body(...)):
    """Grant data access permission to a third party."""
    try:
        if not _dimo:
            return error("DIMO connector not available")
        data_type = data.get("data_type", "")
        grantee = data.get("grantee", "")
        result = await _dimo.grant_permission(vehicle_id, data_type, grantee)
        return ok(data={"success": result, "vehicle_id": vehicle_id, "data_type": data_type, "grantee": grantee})
    except Exception as e:
        logger.error(f"depin_dimo_grant_permission error: {e}")
        return error(str(e))


@router.delete("/api/depin/dimo/vehicles/{vehicle_id}/permissions")
async def depin_dimo_revoke_permission(vehicle_id: str, data: dict = Body(...)):
    """Revoke data access permission from a third party."""
    try:
        if not _dimo:
            return error("DIMO connector not available")
        data_type = data.get("data_type", "")
        grantee = data.get("grantee", "")
        result = await _dimo.revoke_permission(vehicle_id, data_type, grantee)
        return ok(data={"success": result, "vehicle_id": vehicle_id, "data_type": data_type, "grantee": grantee})
    except Exception as e:
        logger.error(f"depin_dimo_revoke_permission error: {e}")
        return error(str(e))


@router.post("/api/depin/dimo/vehicles/{vehicle_id}/rewards")
async def depin_dimo_claim_rewards(vehicle_id: str):
    """Claim accumulated rewards for a vehicle."""
    try:
        if not _dimo:
            return error("DIMO connector not available")
        reward = await _dimo.claim_rewards(vehicle_id)
        return ok(data={"vehicle_id": vehicle_id, "reward": reward})
    except Exception as e:
        logger.error(f"depin_dimo_claim_rewards error: {e}")
        return error(str(e))


@router.get("/api/depin/dimo/stats")
async def depin_dimo_stats():
    """Get DIMO network statistics."""
    try:
        if not _dimo:
            return error("DIMO connector not available")
        stats = _dimo.get_network_stats()
        return ok(data=stats)
    except Exception as e:
        logger.error(f"depin_dimo_stats error: {e}")
        return error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# AGGREGATE
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/depin/status")
async def depin_status():
    """Get aggregate status of all DePIN connectors."""
    try:
        status = {
            "uplink": _uplink.get_network_stats() if _uplink else {"available": False},
            "daylight": _daylight.get_network_stats() if _daylight else {"available": False},
            "dimo": _dimo.get_network_stats() if _dimo else {"available": False},
        }
        return ok(data=status)
    except Exception as e:
        logger.error(f"depin_status error: {e}")
        return error(str(e))
