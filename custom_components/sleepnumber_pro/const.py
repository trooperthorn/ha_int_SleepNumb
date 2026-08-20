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

# BLE identifiers for Sleep Number smart hubs (see docs/BLUETOOTH.md).
# Confirmed on a 360-generation hub (MAC 64:DB:A0:...): the hub advertises this
# service UUID and manufacturer id 20051 (0x4E53, "SN") with a small state
# payload. The Climate 360 uses a different service UUID; both are matched.
BLE_SERVICE_UUID = "ffffd1fd-388d-938b-344a-939d1f6efee0"
BLE_SERVICE_UUID_C360 = "09d23fae-90e6-44c2-95b6-0b3d0f1abf25"
BLE_SERVICE_UUIDS = (BLE_SERVICE_UUID, BLE_SERVICE_UUID_C360)
BLE_MANUFACTURER_ID = 20051  # 0x4E53 = "SN"

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
