"""Support for Mopeka sensors."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import math
from typing import Any

from mopeka_iot_ble import SensorUpdate

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.sensor import sensor_device_info_to_hass_device_info

from . import MopekaConfigEntry
from .const import (
    CONF_CUSTOM_TANK_HEIGHT,
    CONF_MEDIUM_TYPE,
    CONF_TANK_SIZE,
    CONF_TOP_MOUNT,
    DEFAULT_CUSTOM_TANK_HEIGHT,
    DEFAULT_MEDIUM_TYPE,
    HORIZONTAL_TANK_SIZES,
    TANK_SIZE_RANGES,
    TankSize,
)
from .device import device_key_to_bluetooth_entity_key

PARALLEL_UPDATES = 0

SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    "accelerometer_x": SensorEntityDescription(
        key="accelerometer_x",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "accelerometer_y": SensorEntityDescription(
        key="accelerometer_y",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "battery": SensorEntityDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "battery_voltage": SensorEntityDescription(
        key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "medium_type": SensorEntityDescription(
        key="medium_type",
        translation_key="medium_type",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "propane_preset": SensorEntityDescription(
        key="propane_preset",
        translation_key="propane_preset",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "reading_quality": SensorEntityDescription(
        key="reading_quality",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "signal_strength": SensorEntityDescription(
        key="signal_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "tank_level": SensorEntityDescription(
        key="tank_level",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "tank_level_percent": SensorEntityDescription(
        key="tank_level_percent",
        translation_key="tank_level_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "temperature": SensorEntityDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
}

_TANK_LEVEL_PERCENT_KEY = "tank_level_percent"
_MEDIUM_TYPE_KEY = "medium_type"
_PROPANE_PRESET_KEY = "propane_preset"


def _circular_segment_fraction(h: float, diameter: float) -> float:
    """Return the volume fraction (0..1) of a horizontal cylinder filled to height *h*.

    Uses the circular segment area formula:
        A(h) = r² * arccos((r-h)/r) - (r-h) * sqrt(2rh - h²)
    where r = diameter / 2.  The fraction is A(h) / (π * r²).
    """
    r = diameter / 2.0
    if h <= 0.0:
        return 0.0
    if h >= diameter:
        return 1.0
    return (r**2 * math.acos((r - h) / r) - (r - h) * math.sqrt(2 * r * h - h**2)) / (
        math.pi * r**2
    )


def _get_tank_level_range(
    entry_data: Mapping[str, Any],
) -> tuple[float, float, bool] | None:
    """Return the (empty_mm, full_mm, is_horizontal) calibration range.

    Returns None when no percentage sensor should be shown:
    - No tank size configured (legacy/unconfigured entries).
    - Custom size with height set to 0 (user opted out).
    - A preset tank size is selected but medium type is not propane.

    The medium type selected in CONF_MEDIUM_TYPE (step 1 of setup) determines
    which acoustic coefficients mopeka_iot_ble applies when converting raw BLE
    data to mm.  This function enforces that constraint:

    Propane + preset  → TANK_SIZE_RANGES (propane coefficients, preset geometry).
    Propane + Custom  → user-supplied height as full level (propane coefficients
                        only — no other medium is permitted on this path).
    Other medium + Custom → user-supplied height as full level (that medium's
                        coefficients are applied by the library per CONF_MEDIUM_TYPE).
    Other medium + preset → not permitted; preset ranges are propane-specific.

    Top-mount (TD40/TD200) + Custom → inverted range: the sensor measures the
                        decreasing air gap above the liquid surface, so
                        (empty_mm=height, full_mm=0.0) inverts the fill formula.

    Legacy entries without CONF_MEDIUM_TYPE default to propane.
    """
    tank_size = entry_data.get(CONF_TANK_SIZE)
    if tank_size is None:
        return None
    medium_type = entry_data.get(CONF_MEDIUM_TYPE, DEFAULT_MEDIUM_TYPE)
    if tank_size == TankSize.CUSTOM:
        height = entry_data.get(CONF_CUSTOM_TANK_HEIGHT, DEFAULT_CUSTOM_TANK_HEIGHT)
        if height <= 0:
            return None
        if entry_data.get(CONF_TOP_MOUNT, False):
            # Top-mount: reading decreases as tank fills.  Invert by swapping
            # empty/full so the standard formula produces the correct fill %.
            return (float(height), 0.0, False)
        return (0.0, float(height), False)
    # Preset ranges are calibrated for propane coefficients only.
    if medium_type != DEFAULT_MEDIUM_TYPE:
        return None
    tank_range = TANK_SIZE_RANGES.get(tank_size)
    if tank_range is None:
        return None
    return (*tank_range, tank_size in HORIZONTAL_TANK_SIZES)


def make_sensor_update_to_bluetooth_data_update(
    tank_range: tuple[float, float, bool] | None,
    medium_type: str | None,
    propane_preset: str | None,
) -> Callable[[SensorUpdate], PassiveBluetoothDataUpdate]:
    """Return a sensor update converter that optionally synthesizes a tank fill %."""

    def sensor_update_to_bluetooth_data_update(
        sensor_update: SensorUpdate,
    ) -> PassiveBluetoothDataUpdate:
        """Convert a sensor update to a bluetooth data update."""
        entity_descriptions: dict[PassiveBluetoothEntityKey, EntityDescription] = {
            device_key_to_bluetooth_entity_key(device_key): SENSOR_DESCRIPTIONS[
                device_key.key
            ]
            for device_key in sensor_update.entity_descriptions
            if device_key.key in SENSOR_DESCRIPTIONS
        }
        entity_data: dict[PassiveBluetoothEntityKey, str | float | int | None] = {
            device_key_to_bluetooth_entity_key(device_key): sensor_values.native_value  # type: ignore[misc]
            for device_key, sensor_values in sensor_update.entity_values.items()
        }
        entity_names: dict[PassiveBluetoothEntityKey, str | None] = {
            device_key_to_bluetooth_entity_key(device_key): sensor_values.name
            for device_key, sensor_values in sensor_update.entity_values.items()
        }

        # Synthesize a tank fill percentage sensor when a calibrated range is known.
        # Vertical tanks: linear interpolation between empty and full mm.
        # Horizontal tanks: cylindrical cross-section geometry for accurate
        #   volume-based fill percentage.
        if tank_range is not None:
            empty_mm, full_mm, is_horizontal = tank_range
            for device_key, sensor_values in sensor_update.entity_values.items():
                if device_key.key == "tank_level":
                    pct_entity_key = PassiveBluetoothEntityKey(
                        _TANK_LEVEL_PERCENT_KEY, device_key.device_id
                    )
                    entity_descriptions[pct_entity_key] = SENSOR_DESCRIPTIONS[
                        _TANK_LEVEL_PERCENT_KEY
                    ]
                    entity_names[pct_entity_key] = None
                    raw_level = sensor_values.native_value
                    if isinstance(raw_level, (int, float)):
                        if is_horizontal:
                            # Cylindrical geometry: volume fraction is
                            # non-linear with respect to fluid height.
                            frac_empty = _circular_segment_fraction(empty_mm, full_mm)
                            frac_reading = _circular_segment_fraction(
                                raw_level, full_mm
                            )
                            pct = (
                                (frac_reading - frac_empty) / (1.0 - frac_empty) * 100.0
                            )
                        else:
                            # Vertical / custom: linear interpolation.
                            pct = (raw_level - empty_mm) / (full_mm - empty_mm) * 100.0
                        entity_data[pct_entity_key] = round(
                            min(100.0, max(0.0, pct)), 1
                        )
                    else:
                        entity_data[pct_entity_key] = None

        # Inject a diagnostic sensor that reflects the configured medium type.
        if medium_type is not None:
            for device_id in sensor_update.devices:
                med_key = PassiveBluetoothEntityKey(_MEDIUM_TYPE_KEY, device_id)
                entity_descriptions[med_key] = SENSOR_DESCRIPTIONS[_MEDIUM_TYPE_KEY]
                entity_data[med_key] = medium_type
                entity_names[med_key] = None

        # Inject a diagnostic sensor that reflects the configured propane preset.
        if medium_type == "propane" and propane_preset is not None:
            for device_id in sensor_update.devices:
                preset_key = PassiveBluetoothEntityKey(_PROPANE_PRESET_KEY, device_id)
                entity_descriptions[preset_key] = SENSOR_DESCRIPTIONS[
                    _PROPANE_PRESET_KEY
                ]
                entity_data[preset_key] = propane_preset
                entity_names[preset_key] = None

        return PassiveBluetoothDataUpdate(
            devices={
                device_id: sensor_device_info_to_hass_device_info(device_info)
                for device_id, device_info in sensor_update.devices.items()
            },
            entity_descriptions=entity_descriptions,
            entity_data=entity_data,
            entity_names=entity_names,
        )

    return sensor_update_to_bluetooth_data_update


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MopekaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Mopeka BLE sensors."""
    coordinator = entry.runtime_data
    tank_range = _get_tank_level_range(entry.data)
    medium_type = entry.data.get(CONF_MEDIUM_TYPE)
    propane_preset = entry.data.get(CONF_TANK_SIZE)
    processor = PassiveBluetoothDataProcessor(
        make_sensor_update_to_bluetooth_data_update(
            tank_range, medium_type, propane_preset
        )
    )
    entry.async_on_unload(
        processor.async_add_entities_listener(
            MopekaBluetoothSensorEntity, async_add_entities
        )
    )
    entry.async_on_unload(coordinator.async_register_processor(processor))


class MopekaBluetoothSensorEntity(
    PassiveBluetoothProcessorEntity[
        PassiveBluetoothDataProcessor[str | float | int | None, SensorUpdate]
    ],
    SensorEntity,
):
    """Representation of a Mopeka sensor."""

    @property
    def native_value(self) -> str | int | float | None:
        """Return the native value."""
        return self.processor.entity_data.get(self.entity_key)
