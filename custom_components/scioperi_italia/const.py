"""Costanti per Scioperi Italia V2."""

DOMAIN = "scioperi_italia"

# Configuration
CONF_RSS_URL = "rss_url"
CONF_REGION_FILTER = "region_filter"
CONF_SECTOR_FILTER = "sector_filter"
CONF_RADIUS = "radius"
CONF_FAVORITE_SECTORS = "favorite_sectors"
CONF_ENABLE_NOTIFICATIONS = "enable_notifications"
CONF_WORK_LOCATION = "work_location"
CONF_NOTIFICATION_TIME = "notification_time"

DEFAULT_RSS_URL = "https://scioperi.mit.gov.it/mit2/public/scioperi/rss"

# Update intervals
UPDATE_INTERVAL_HOURS = 6
UPDATE_INTERVAL_SECONDS = UPDATE_INTERVAL_HOURS * 3600

# Radius options (in km)
RADIUS_OPTIONS = [5, 10, 25, 50, 100, 500]  # 500 = Italia intera
DEFAULT_RADIUS = 50

# Notification timing options (hours before strike)
NOTIFICATION_TIMES = [24, 48, 72, 168]  # 1 day, 2 days, 3 days, 1 week
DEFAULT_NOTIFICATION_TIME = 24

# Settori (dal feed RSS reale)
SECTORS = [
    "Trasporto pubblico locale",
    "Aereo",
    "Ferroviario",
    "Trasporto merci e logistica",
    "Marittimo",
    "Tutti"
]

# Rilevanza
RELEVANCE_TYPES = [
    "Nazionale",
    "Regionale", 
    "Provinciale",
    "Locale",
    "Territoriale",
    "Interregionale"
]

# Regioni italiane con coordinate approssimative centro
REGIONS = {
    "Abruzzo": {"lat": 42.3506, "lon": 13.3995},
    "Basilicata": {"lat": 40.6386, "lon": 15.8055},
    "Calabria": {"lat": 38.9101, "lon": 16.5987},
    "Campania": {"lat": 40.8333, "lon": 14.2500},
    "Emilia-Romagna": {"lat": 44.4949, "lon": 11.3426},
    "Friuli-Venezia Giulia": {"lat": 45.6361, "lon": 13.8043},
    "Lazio": {"lat": 41.9028, "lon": 12.4964},
    "Liguria": {"lat": 44.4056, "lon": 8.9463},
    "Lombardia": {"lat": 45.4642, "lon": 9.1900},
    "Marche": {"lat": 43.6158, "lon": 13.5189},
    "Molise": {"lat": 41.5603, "lon": 14.6587},
    "Piemonte": {"lat": 45.0522, "lon": 7.5153},
    "Puglia": {"lat": 41.1171, "lon": 16.8719},
    "Sardegna": {"lat": 40.1209, "lon": 9.0129},
    "Sicilia": {"lat": 37.5999, "lon": 14.0154},
    "Toscana": {"lat": 43.7711, "lon": 11.2486},
    "Trentino-Alto Adige": {"lat": 46.0664, "lon": 11.1257},
    "Umbria": {"lat": 42.9380, "lon": 12.6147},
    "Valle d'Aosta": {"lat": 45.7376, "lon": 7.3206},
    "Veneto": {"lat": 45.4408, "lon": 12.3155},
}

# Province principali con coordinate
PROVINCES = {
    "Alba": {"lat": 44.7007, "lon": 8.0357},
    "Torino": {"lat": 45.0703, "lon": 7.6869},
    "Milano": {"lat": 45.4642, "lon": 9.1900},
    "Roma": {"lat": 41.9028, "lon": 12.4964},
    "Napoli": {"lat": 40.8518, "lon": 14.2681},
    "Palermo": {"lat": 38.1157, "lon": 13.3615},
    # Aggiungi altre se necessario
}

# Sensor types
SENSOR_TYPE_COUNT = "count"
SENSOR_TYPE_NEXT = "next"
SENSOR_TYPE_TODAY = "today"
SENSOR_TYPE_TOMORROW = "tomorrow"
SENSOR_TYPE_NEARBY = "nearby"
SENSOR_TYPE_FAVORITES = "favorites"

# Attributes
ATTR_STRIKES = "strikes"
ATTR_SECTOR = "sector"
ATTR_REGION = "region"
ATTR_PROVINCE = "province"
ATTR_START_DATE = "start_date"
ATTR_END_DATE = "end_date"
ATTR_RELEVANCE = "relevance"
ATTR_MODALITY = "modality"
ATTR_UNIONS = "unions"
ATTR_CATEGORY = "category"
ATTR_PROCLAMATION_DATE = "proclamation_date"
ATTR_DISTANCE = "distance"
ATTR_LATITUDE = "latitude"
ATTR_LONGITUDE = "longitude"
ATTR_IN_RADIUS = "in_radius"
ATTR_NOTIFICATION_SENT = "notification_sent"

# Services
SERVICE_CHECK_ROUTE = "check_route"
SERVICE_NOTIFY = "notify_strike"
SERVICE_REFRESH = "refresh_data"

# Events
EVENT_STRIKE_DETECTED = f"{DOMAIN}_strike_detected"
EVENT_STRIKE_TOMORROW = f"{DOMAIN}_strike_tomorrow"
EVENT_STRIKE_NEARBY = f"{DOMAIN}_strike_nearby"

# Icons
ICON_DEFAULT = "mdi:alert-circle"
ICON_BUS = "mdi:bus"
ICON_TRAIN = "mdi:train"
ICON_AIRPLANE = "mdi:airplane"
ICON_SHIP = "mdi:ferry"
ICON_TRUCK = "mdi:truck"
ICON_LOCATION = "mdi:map-marker-radius"
