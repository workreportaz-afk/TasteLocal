"""
Free geolocation "near me" support -- no Google Maps Distance Matrix API
needed. Straight-line (great-circle) distance via the haversine formula,
computed in Python since MySQL's spatial functions add setup complexity
this project's scale doesn't need.
"""
from math import radians, sin, cos, sqrt, atan2

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1, lng1, lat2, lng2):
    """Great-circle distance between two lat/lng points, in kilometres."""
    lat1, lng1, lat2, lng2 = map(radians, [float(lat1), float(lng1), float(lat2), float(lng2)])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return EARTH_RADIUS_KM * 2 * atan2(sqrt(a), sqrt(1 - a))
