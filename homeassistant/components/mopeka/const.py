"""Constants for the Mopeka integration."""

from enum import StrEnum
from typing import Final

from mopeka_iot_ble import MediumType

DOMAIN = "mopeka"

CONF_CUSTOM_TANK_HEIGHT: Final = "custom_tank_height"
CONF_MEDIUM_TYPE: Final = "medium_type"
CONF_TANK_SIZE: Final = "tank_size"

DEFAULT_MEDIUM_TYPE: Final = MediumType.PROPANE.value
DEFAULT_CUSTOM_TANK_HEIGHT: Final = 0


class TankSize(StrEnum):
    """Predefined tank sizes matching the Mopeka app presets."""

    LB_20 = "20lb"
    LB_30 = "30lb"
    LB_40 = "40lb"
    LB_100 = "100lb"
    GAL_100_H = "100gal_h"
    GAL_500_H = "500gal_h"
    GAL_1000_H = "1000gal_h"
    GAL_12_2_RV_H = "12_2gal_rv_h"
    GAL_16_RV_H = "16gal_rv_h"
    GAL_20_3_RV_H = "20_3gal_rv_h"
    GAL_29_3_RV_H = "29_3gal_rv_h"
    CUSTOM = "custom"


DEFAULT_TANK_SIZE: Final = TankSize.LB_20

# Minimum readable fluid height in mm.  Accounts for the physical curvature at the
# bottom of the tank and the ultrasonic sensor's dead zone.
TANK_EMPTY_MM: Final = 38.1

# Physical (empty_mm, full_mm) tank dimensions in millimeters.
# The mopeka_iot_ble library already converts the raw sensor reading into the
# physical fluid height in mm by applying a temperature-dependent speed-of-sound
# polynomial for the configured medium type.  Therefore these ranges are real
# tank measurements and work correctly regardless of the medium type.
#
# Vertical tank full heights come from standard US DOT propane cylinder liquid
# column heights.  Horizontal / RV ASME full heights are the inner diameter of
# the tank (the maximum fluid height when the tank is on its side).
#
# Fill % = clamp((reading - empty_mm) / (full_mm - empty_mm) * 100, 0, 100).
TANK_SIZE_RANGES: Final[dict[str, tuple[float, float]]] = {
    TankSize.LB_20: (TANK_EMPTY_MM, 254.0),
    TankSize.LB_30: (TANK_EMPTY_MM, 381.0),
    TankSize.LB_40: (TANK_EMPTY_MM, 508.0),
    TankSize.LB_100: (TANK_EMPTY_MM, 813.0),
    TankSize.GAL_100_H: (TANK_EMPTY_MM, 600.7),
    TankSize.GAL_500_H: (TANK_EMPTY_MM, 939.8),
    TankSize.GAL_1000_H: (TANK_EMPTY_MM, 1025.7),
    TankSize.GAL_12_2_RV_H: (TANK_EMPTY_MM, 301.0),
    TankSize.GAL_16_RV_H: (TANK_EMPTY_MM, 346.7),
    TankSize.GAL_20_3_RV_H: (TANK_EMPTY_MM, 393.7),
    TankSize.GAL_29_3_RV_H: (TANK_EMPTY_MM, 369.6),
}

# Tank sizes that are mounted horizontally.  For these tanks the full_mm value
# is the internal diameter and the relationship between fluid height and fill
# volume is non-linear (circular cross-section geometry).
HORIZONTAL_TANK_SIZES: Final[frozenset[str]] = frozenset(
    {
        TankSize.GAL_100_H,
        TankSize.GAL_500_H,
        TankSize.GAL_1000_H,
        TankSize.GAL_12_2_RV_H,
        TankSize.GAL_16_RV_H,
        TankSize.GAL_20_3_RV_H,
        TankSize.GAL_29_3_RV_H,
    }
)
