"""Constants for the Russound RNET (CAM6.6) integration."""

DOMAIN = "russrnet"

DEFAULT_NAME = "Russound CAM6.6"

CONF_ZONES = "zones"
CONF_SOURCES = "sources"

# RNET has no fixed default port - depends entirely on your
# serial-to-TCP bridge configuration (ser2net, GC-100, etc.)
# Common bridge defaults are 9999 or 8899, but there is no
# universal standard, so no default is assumed here.

# CAM6.6 supports up to 6 zones and 6 sources per controller.
MAX_ZONES = 6
MAX_SOURCES = 6

# Russound RNET volume range
MIN_VOLUME = 0
MAX_VOLUME = 50
