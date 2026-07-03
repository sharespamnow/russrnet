"""Constants for the Russound RNET (CAM6.6) integration."""

DOMAIN = "russrnet"

DEFAULT_NAME = "Russound"

CONF_ZONES = "zones"
CONF_SOURCES = "sources"

# CAM6.6 supports up to 6 zones and 6 sources per controller.
ZONES_PER_CONTROLLER = 6
MAX_SOURCES = 6

# RNET volume range used by aiorussound's RussoundRNETClient
MIN_VOLUME = 0
MAX_VOLUME = 50
