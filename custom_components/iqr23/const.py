"""Constants for the iQ R23 integration."""

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "iqr23"
MANUFACTURER = "iQ vytápění"
MODEL = "iQ R23"

CARD_URL = f"/{DOMAIN}/iqr23-card.js"

PLATFORMS = [Platform.BINARY_SENSOR, Platform.NUMBER, Platform.SELECT, Platform.SENSOR]

CONF_FIRMWARE_VERSION = "firmware_version"
CONF_MASTER_PASSWORD = "master_password"
CONF_MODULES = "modules"

DEFAULT_MASTER_PASSWORD = "Servis254"

UPDATE_INTERVAL = timedelta(seconds=15)
# Number of consecutive failed polls tolerated before entities become unavailable.
MAX_CONSECUTIVE_FAILURES = 3
