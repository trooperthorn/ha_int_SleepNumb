"""Small compatibility shims so the integration targets the latest Home
Assistant while still importing on slightly older cores used for testing."""

from __future__ import annotations

try:  # HA 2025.2+
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
except ImportError:  # older cores
    from homeassistant.helpers.entity_platform import (
        AddEntitiesCallback as AddConfigEntryEntitiesCallback,
    )

__all__ = ["AddConfigEntryEntitiesCallback"]
