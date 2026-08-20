"""Constants for the Sleep Number (SleepIQ) Local-First integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "sleepnumber_pro"

MANUFACTURER = "Sleep Number"

# Config
CONF_LOCAL_HOST = "local_host"  # optional on-hub bridge host (Phase 2)

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

ICON_OCCUPIED = "mdi:bed"
ICON_EMPTY = "mdi:bed-empty"
