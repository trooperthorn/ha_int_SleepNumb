"""Constants for the Sleep Number (SleepIQ) Local-First integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "sleepnumber_pro"

MANUFACTURER = "Sleep Number"

# Config
CONF_LOCAL_HOST = "local_host"    # optional on-hub bridge host (Phase 2)
CONF_LOCAL_PORT = "local_port"    # bridge port (default 8765)
CONF_LOCAL_TOKEN = "local_token"  # optional bridge shared secret
CONF_BLE_ADDRESS = "ble_address"  # optional BLE address of the bed hub (Phase 2b)

# Custom GATT service advertised by Sleep Number smart hubs (observed on the
# Climate 360; used as the BLE discovery matcher and a starting point for GATT
# capture on other models -- see docs/BLUETOOTH.md).
BLE_SERVICE_UUID = "09d23fae-90e6-44c2-95b6-0b3d0f1abf25"

# Update cadences.  The bed sensor plane changes often; pause / responsive-air
# rarely; sleep-health once a night.
STATUS_INTERVAL = timedelta(seconds=60)
SETTINGS_INTERVAL = timedelta(minutes=5)
SLEEP_DATA_INTERVAL = timedelta(hours=1)

# Entity keys (translation keys live in strings.json)
IS_IN_BED = "is_in_bed"
PRESSURE = "pressure"
SLEEP_NUMBER = "sleep_number"
FAVORITE_SLEEP_NUMBER = "favorite_sleep_number"
SLEEP_SCORE = "sleep_score"
SLEEP_DURATION = "sleep_duration"
HEART_RATE = "heart_rate"
RESPIRATORY_RATE = "respiratory_rate"
HRV = "hrv"
RESTFUL = "restful"
RESTLESS = "restless"
RESPONSIVE_AIR = "responsive_air"
PRIVACY = "privacy"
CONNECTION = "connection"

# Transport labels (also the state of the connection sensor)
SOURCE_LOCAL = "local"
SOURCE_CLOUD = "cloud"

ICON_OCCUPIED = "mdi:bed"
ICON_EMPTY = "mdi:bed-empty"
