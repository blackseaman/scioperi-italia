"""Utility functions per Scioperi Italia."""
import logging
from math import radians, cos, sin, asin, sqrt
from typing import Tuple

_LOGGER = logging.getLogger(__name__)


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcola distanza tra due coordinate usando formula Haversine.
    
    Args:
        lat1, lon1: Coordinate punto 1 (gradi)
        lat2, lon2: Coordinate punto 2 (gradi)
    
    Returns:
        Distanza in chilometri
    """
    # Converti a radianti
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Formula Haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Raggio della Terra in km
    r = 6371
    
    return round(c * r, 2)


def get_region_coordinates(region: str) -> Tuple[float, float] | None:
    """Ottieni coordinate centro regione."""
    from .const import REGIONS
    
    region_data = REGIONS.get(region)
    if region_data:
        return region_data["lat"], region_data["lon"]
    return None


def get_province_coordinates(province: str) -> Tuple[float, float] | None:
    """Ottieni coordinate provincia."""
    from .const import PROVINCES
    
    province_data = PROVINCES.get(province)
    if province_data:
        return province_data["lat"], province_data["lon"]
    return None


def extract_coordinates(strike: dict) -> Tuple[float, float] | None:
    """
    Estrai coordinate da sciopero.
    Prova prima provincia, poi regione.
    """
    # Prova provincia
    province = strike.get("province", "").strip()
    if province:
        coords = get_province_coordinates(province)
        if coords:
            return coords
    
    # Fallback su regione
    region = strike.get("region", "").strip()
    if region:
        coords = get_region_coordinates(region)
        if coords:
            return coords
    
    return None


def is_strike_nearby(
    strike: dict,
    home_lat: float,
    home_lon: float,
    radius_km: float
) -> Tuple[bool, float]:
    """
    Verifica se sciopero è nel raggio.
    
    Returns:
        (is_nearby, distance_km)
    """
    coords = extract_coordinates(strike)
    
    if not coords:
        # Se nazionale o senza coordinate, considera sempre vicino
        relevance = strike.get("relevance", "").lower()
        if "nazionale" in relevance or "italia" in relevance:
            return (True, 0.0)
        return (False, 999999.0)
    
    distance = calculate_distance(home_lat, home_lon, coords[0], coords[1])
    
    return (distance <= radius_km, distance)


def format_distance(distance_km: float) -> str:
    """Formatta distanza in modo leggibile."""
    if distance_km == 0:
        return "Nazionale"
    elif distance_km < 1:
        return f"{int(distance_km * 1000)}m"
    elif distance_km < 10:
        return f"{distance_km:.1f}km"
    else:
        return f"{int(distance_km)}km"


def get_home_coordinates(hass) -> Tuple[float, float] | None:
    """Ottieni coordinate casa da Home Assistant."""
    try:
        return (
            hass.config.latitude,
            hass.config.longitude
        )
    except Exception as e:
        _LOGGER.error("Cannot get home coordinates: %s", e)
        return None


def should_notify(strike: dict, hours_before: int) -> bool:
    """
    Verifica se deve notificare per questo sciopero.
    
    Args:
        strike: Dati sciopero
        hours_before: Ore prima dello sciopero
    
    Returns:
        True se deve notificare
    """
    from datetime import datetime, timedelta
    
    start_date = strike.get("start_date")
    if not start_date:
        return False
    
    now = datetime.now()
    target_time = start_date - timedelta(hours=hours_before)
    
    # Notifica se siamo nel giorno target e non abbiamo già notificato
    return (
        now.date() == target_time.date() and
        not strike.get("notification_sent", False)
    )
