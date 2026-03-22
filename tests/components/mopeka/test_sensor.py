"""Test the Mopeka sensors."""

import math

from homeassistant.components.mopeka.const import (
    CONF_CUSTOM_TANK_HEIGHT,
    CONF_MEDIUM_TYPE,
    CONF_TANK_CAPACITY,
    CONF_TANK_SIZE,
    CONF_TOP_MOUNT,
    DOMAIN,
    HORIZONTAL_TANK_SIZES,
    IBC_TANK_SIZE_RANGES,
    TANK_EMPTY_MM,
    TANK_SIZE_CAPACITIES,
    TANK_SIZE_RANGES,
    MediumType,
    TankSize,
)
from homeassistant.components.sensor import ATTR_STATE_CLASS
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    STATE_UNKNOWN,
    UnitOfLength,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant

from . import (
    PRO_GOOD_SIGNAL_SERVICE_INFO,
    PRO_SERVICE_INFO,
    PRO_UNUSABLE_SIGNAL_SERVICE_INFO,
    TD_GOOD_SIGNAL_SERVICE_INFO,
    TD_SERVICE_INFO,
)

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info

# Raw tank level reported by PRO_GOOD_SIGNAL_SERVICE_INFO
_GOOD_SIGNAL_LEVEL_MM = 341


def _circular_segment_fraction(h: float, diameter: float) -> float:
    """Return the volume fraction (0..1) of a horizontal cylinder filled to height h."""
    r = diameter / 2.0
    if h <= 0.0:
        return 0.0
    if h >= diameter:
        return 1.0
    return (r**2 * math.acos((r - h) / r) - (r - h) * math.sqrt(2 * r * h - h**2)) / (
        math.pi * r**2
    )


def _expected_fill_percent(level_mm: int, tank_size: TankSize) -> float:
    """Return the expected fill percentage for a given level and preset tank size."""
    empty_mm, full_mm = TANK_SIZE_RANGES[tank_size]
    if tank_size in HORIZONTAL_TANK_SIZES:
        frac_empty = _circular_segment_fraction(empty_mm, full_mm)
        frac_reading = _circular_segment_fraction(level_mm, full_mm)
        pct = (frac_reading - frac_empty) / (1.0 - frac_empty) * 100.0
    else:
        pct = (level_mm - empty_mm) / (full_mm - empty_mm) * 100.0
    return round(min(100.0, max(0.0, pct)), 1)


async def test_sensors_unusable_signal(hass: HomeAssistant) -> None:
    """Test setting up creates the sensors when there is unusable signal."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 0
    inject_bluetooth_service_info(hass, PRO_UNUSABLE_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 4

    temp_sensor = hass.states.get("sensor.pro_plus_eeff_temperature")
    temp_sensor_attrs = temp_sensor.attributes
    assert temp_sensor.state == "30"
    assert temp_sensor_attrs[ATTR_FRIENDLY_NAME] == "Pro Plus EEFF Temperature"
    assert temp_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    assert temp_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    tank_sensor = hass.states.get("sensor.pro_plus_eeff_tank_level")
    tank_sensor_attrs = tank_sensor.attributes
    assert tank_sensor.state == STATE_UNKNOWN
    assert tank_sensor_attrs[ATTR_FRIENDLY_NAME] == "Pro Plus EEFF Tank Level"
    assert tank_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == UnitOfLength.MILLIMETERS
    assert tank_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_poor_signal(hass: HomeAssistant) -> None:
    """Test setting up creates the sensors when there is poor signal."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 0
    inject_bluetooth_service_info(hass, PRO_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 4

    temp_sensor = hass.states.get("sensor.pro_plus_eeff_temperature")
    temp_sensor_attrs = temp_sensor.attributes
    assert temp_sensor.state == "30"
    assert temp_sensor_attrs[ATTR_FRIENDLY_NAME] == "Pro Plus EEFF Temperature"
    assert temp_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    assert temp_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    tank_sensor = hass.states.get("sensor.pro_plus_eeff_tank_level")
    tank_sensor_attrs = tank_sensor.attributes
    assert tank_sensor.state == "0"
    assert tank_sensor_attrs[ATTR_FRIENDLY_NAME] == "Pro Plus EEFF Tank Level"
    assert tank_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == UnitOfLength.MILLIMETERS
    assert tank_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_good_signal(hass: HomeAssistant) -> None:
    """Test setting up creates the sensors when there is good signal."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 0
    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 4

    temp_sensor = hass.states.get("sensor.pro_plus_eeff_temperature")
    temp_sensor_attrs = temp_sensor.attributes
    assert temp_sensor.state == "27"
    assert temp_sensor_attrs[ATTR_FRIENDLY_NAME] == "Pro Plus EEFF Temperature"
    assert temp_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    assert temp_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    tank_sensor = hass.states.get("sensor.pro_plus_eeff_tank_level")
    tank_sensor_attrs = tank_sensor.attributes
    assert tank_sensor.state == "341"
    assert tank_sensor_attrs[ATTR_FRIENDLY_NAME] == "Pro Plus EEFF Tank Level"
    assert tank_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == UnitOfLength.MILLIMETERS
    assert tank_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_good_signal_20lb_tank(hass: HomeAssistant) -> None:
    """Test tank fill percentage for a 20 lb preset.

    341 mm exceeds the 20 lb full level (254 mm), so the result is capped at 100%.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_TANK_SIZE: TankSize.LB_20},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 6

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    # 341 mm exceeds the 20 lb full level (254 mm), so the result is capped at 100%.
    assert float(pct_sensor.state) == 100.0
    assert pct_sensor.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE
    assert pct_sensor.attributes[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_good_signal_30lb_tank(hass: HomeAssistant) -> None:
    """Test tank fill percentage for a 30 lb preset (empty=38.1, full=381).

    Expected: (341 - 38.1) / (381 - 38.1) * 100 ≈ 88.3%.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_TANK_SIZE: TankSize.LB_30},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 6

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    assert float(pct_sensor.state) == _expected_fill_percent(
        _GOOD_SIGNAL_LEVEL_MM, TankSize.LB_30
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_good_signal_40lb_tank(hass: HomeAssistant) -> None:
    """Test tank fill percentage for a 40 lb preset (empty=38.1, full=508).

    Expected: (341 - 38.1) / (508 - 38.1) * 100 ≈ 64.5%.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_TANK_SIZE: TankSize.LB_40},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 6

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    assert float(pct_sensor.state) == _expected_fill_percent(
        _GOOD_SIGNAL_LEVEL_MM, TankSize.LB_40
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_good_signal_custom_tank(hass: HomeAssistant) -> None:
    """Test tank fill percentage for a custom tank (empty=0, full=user_height).

    Uses height=682 mm: 341 / 682 * 100 = 50.0%.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_TANK_SIZE: TankSize.CUSTOM,
            CONF_CUSTOM_TANK_HEIGHT: 682,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 5

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    assert float(pct_sensor.state) == 50.0

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_custom_zero_height_disables_percent(
    hass: HomeAssistant,
) -> None:
    """Test that Custom with height=0 does not create a percentage sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_TANK_SIZE: TankSize.CUSTOM,
            CONF_CUSTOM_TANK_HEIGHT: 0,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 4
    assert hass.states.get("sensor.pro_plus_eeff_tank_fill") is None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_fill_percent_capped_at_100(hass: HomeAssistant) -> None:
    """Test that fill percentage is capped at 100% when reading exceeds full level."""
    # Custom height of 100 mm; reading of 341 mm far exceeds it.
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_TANK_SIZE: TankSize.CUSTOM,
            CONF_CUSTOM_TANK_HEIGHT: 100,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    assert float(pct_sensor.state) == 100.0

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_good_signal_100lb_tank(hass: HomeAssistant) -> None:
    """Test tank fill percentage for a 100 lb preset (empty=38.1, full=813).

    Expected: (341 - 38.1) / (813 - 38.1) * 100 ≈ 39.1%.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_TANK_SIZE: TankSize.LB_100},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 6

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    assert float(pct_sensor.state) == _expected_fill_percent(
        _GOOD_SIGNAL_LEVEL_MM, TankSize.LB_100
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_good_signal_100gal_h_tank(hass: HomeAssistant) -> None:
    """Test tank fill percentage for a 100 gal horizontal preset (diameter=600.7).

    Uses cylindrical cross-section geometry for volume-based fill calculation.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_TANK_SIZE: TankSize.GAL_100_H},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 6

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    assert float(pct_sensor.state) == _expected_fill_percent(
        _GOOD_SIGNAL_LEVEL_MM, TankSize.GAL_100_H
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_good_signal_500gal_h_tank(hass: HomeAssistant) -> None:
    """Test tank fill percentage for a 500 gal horizontal preset (diameter=939.8).

    Uses cylindrical cross-section geometry for volume-based fill calculation.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_TANK_SIZE: TankSize.GAL_500_H},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 6

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    assert float(pct_sensor.state) == _expected_fill_percent(
        _GOOD_SIGNAL_LEVEL_MM, TankSize.GAL_500_H
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_good_signal_1000gal_h_tank(hass: HomeAssistant) -> None:
    """Test tank fill percentage for a 1000 gal horizontal preset (diameter=1025.7).

    Uses cylindrical cross-section geometry for volume-based fill calculation.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_TANK_SIZE: TankSize.GAL_1000_H},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 6

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    assert float(pct_sensor.state) == _expected_fill_percent(
        _GOOD_SIGNAL_LEVEL_MM, TankSize.GAL_1000_H
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_unusable_signal_with_tank_size(hass: HomeAssistant) -> None:
    """Test that the fill percentage shows unknown when the signal is unusable."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_TANK_SIZE: TankSize.LB_30},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_UNUSABLE_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 6

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    assert pct_sensor.state == STATE_UNKNOWN

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_good_signal_12_2gal_rv_h_tank(hass: HomeAssistant) -> None:
    """Test tank fill percentage for a 12.2 gal RV horizontal ASME preset.

    341 mm exceeds the full level (301.0 mm), so the result is capped at 100%.
    Uses cylindrical cross-section geometry.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_TANK_SIZE: TankSize.GAL_12_2_RV_H},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 6

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    # 341 mm exceeds the 12.2 gal RV h full level (301.0 mm), so the result is capped at 100%.
    assert float(pct_sensor.state) == 100.0

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_good_signal_16gal_rv_h_tank(hass: HomeAssistant) -> None:
    """Test tank fill percentage for a 16 gal RV horizontal ASME preset (diameter=346.7).

    Uses cylindrical cross-section geometry for volume-based fill calculation.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_TANK_SIZE: TankSize.GAL_16_RV_H},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 6

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    assert float(pct_sensor.state) == _expected_fill_percent(
        _GOOD_SIGNAL_LEVEL_MM, TankSize.GAL_16_RV_H
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_good_signal_20_3gal_rv_h_tank(hass: HomeAssistant) -> None:
    """Test tank fill percentage for a 20.3 gal RV horizontal ASME preset (diameter=393.7).

    Uses cylindrical cross-section geometry for volume-based fill calculation.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_TANK_SIZE: TankSize.GAL_20_3_RV_H},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 6

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    assert float(pct_sensor.state) == _expected_fill_percent(
        _GOOD_SIGNAL_LEVEL_MM, TankSize.GAL_20_3_RV_H
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_good_signal_29_3gal_rv_h_tank(hass: HomeAssistant) -> None:
    """Test tank fill percentage for a 29.3 gal RV horizontal ASME preset (diameter=369.6).

    Uses cylindrical cross-section geometry for volume-based fill calculation.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_TANK_SIZE: TankSize.GAL_29_3_RV_H},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 6

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    assert float(pct_sensor.state) == _expected_fill_percent(
        _GOOD_SIGNAL_LEVEL_MM, TankSize.GAL_29_3_RV_H
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_medium_type_diagnostic(hass: HomeAssistant) -> None:
    """Test that the medium type diagnostic sensor appears when CONF_MEDIUM_TYPE is set."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_MEDIUM_TYPE: MediumType.PROPANE.value},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    # 4 base sensors + medium_type (no tank size → no fill %)
    assert len(hass.states.async_all("sensor")) == 5

    med_sensor = hass.states.get("sensor.pro_plus_eeff_medium_type")
    assert med_sensor is not None
    assert med_sensor.state == MediumType.PROPANE.value

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_propane_preset_diagnostic(hass: HomeAssistant) -> None:
    """Test that the propane preset diagnostic sensor appears for propane entries."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_MEDIUM_TYPE: MediumType.PROPANE.value,
            CONF_TANK_SIZE: TankSize.LB_30,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    # 4 base sensors + tank fill + medium type + propane preset
    assert len(hass.states.async_all("sensor")) == 8

    preset_sensor = hass.states.get("sensor.pro_plus_eeff_propane_preset")
    assert preset_sensor is not None
    assert preset_sensor.state == TankSize.LB_30

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_propane_preset_only_for_propane(hass: HomeAssistant) -> None:
    """Test that preset tank ranges are not used for non-propane media.

    TANK_SIZE_RANGES values are calibrated against propane acoustic coefficients.
    When the medium type is not propane the library applies different coefficients,
    producing mm readings that are incompatible with those ranges.  No fill %
    sensor should be created in this case.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_MEDIUM_TYPE: MediumType.GASOLINE.value,
            CONF_TANK_SIZE: TankSize.LB_30,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    # 4 base sensors + medium type; no fill % (preset blocked for non-propane)
    assert len(hass.states.async_all("sensor")) == 5
    assert hass.states.get("sensor.pro_plus_eeff_tank_fill") is None
    assert hass.states.get("sensor.pro_plus_eeff_propane_preset") is None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_medium_type_non_propane(hass: HomeAssistant) -> None:
    """Test the medium type diagnostic sensor for a non-propane medium with custom height."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_MEDIUM_TYPE: MediumType.FRESH_WATER.value,
            CONF_TANK_SIZE: TankSize.CUSTOM,
            CONF_CUSTOM_TANK_HEIGHT: 500,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    # 4 base + medium_type + tank_fill = 6
    assert len(hass.states.async_all("sensor")) == 6

    med_sensor = hass.states.get("sensor.pro_plus_eeff_medium_type")
    assert med_sensor is not None
    assert med_sensor.state == MediumType.FRESH_WATER.value

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_medium_type_impacts_tank_level(hass: HomeAssistant) -> None:
    """Test that medium type changes tank level conversion for the same reading.

    The mopeka_iot_ble parser applies a temperature-dependent polynomial per
    medium type. For PRO_GOOD_SIGNAL_SERVICE_INFO this yields:
    - propane: 341 mm
    - fresh water: 711 mm
    """
    propane_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_MEDIUM_TYPE: MediumType.PROPANE.value},
    )
    propane_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(propane_entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()

    propane_tank_sensor = hass.states.get("sensor.pro_plus_eeff_tank_level")
    assert propane_tank_sensor is not None
    assert propane_tank_sensor.state == "341"

    assert await hass.config_entries.async_unload(propane_entry.entry_id)
    await hass.async_block_till_done()

    freshwater_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_MEDIUM_TYPE: MediumType.FRESH_WATER.value},
    )
    freshwater_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(freshwater_entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()

    freshwater_tank_sensor = hass.states.get("sensor.pro_plus_eeff_tank_level")
    assert freshwater_tank_sensor is not None
    assert freshwater_tank_sensor.state == "711"

    assert await hass.config_entries.async_unload(freshwater_entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_medium_type_absent_for_legacy_entries(
    hass: HomeAssistant,
) -> None:
    """Test that legacy entries without CONF_MEDIUM_TYPE have no medium type sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        # No CONF_MEDIUM_TYPE — simulates a pre-existing legacy config entry
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 4
    assert hass.states.get("sensor.pro_plus_eeff_medium_type") is None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


# ---------------------------------------------------------------------------
# Top-mount (TD40/TD200) sensor tests
# ---------------------------------------------------------------------------

# Air-gap reading produced by TD_GOOD_SIGNAL_SERVICE_INFO (raw=950, raw_temp=67,
# AIR coefficients: c0=0.153096, c1=0.000327, c2=-0.000000294).
# mm = int(950 * (0.153096 + 0.000327*67 + (-0.000000294)*67²)) = int(165.0) = 165
_TD_GOOD_SIGNAL_AIR_GAP_MM = 165


async def test_sensors_top_mount_fill_percent(hass: HomeAssistant) -> None:
    """Test fill% inversion for a TD40/TD200 top-mount sensor.

    The sensor measures a decreasing air gap above the liquid surface.
    fill% = (tank_height - air_gap) / tank_height * 100.
    """
    tank_height_mm = 400
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:75:10",
        data={
            CONF_MEDIUM_TYPE: MediumType.AIR.value,
            CONF_TANK_SIZE: TankSize.CUSTOM,
            CONF_CUSTOM_TANK_HEIGHT: tank_height_mm,
            CONF_TOP_MOUNT: True,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, TD_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()

    # Expect: battery, reading_quality, tank_level, temperature (4 base enabled),
    # tank_level_percent (synthesized), medium_type (injected) = 6 sensors.
    # battery_voltage and signal_strength are disabled by default.
    assert len(hass.states.async_all("sensor")) == 6

    tank_level_sensor = hass.states.get("sensor.td40_td200_7510_tank_level")
    assert tank_level_sensor is not None
    assert tank_level_sensor.state == str(_TD_GOOD_SIGNAL_AIR_GAP_MM)

    # fill% = (400 - 165) / 400 * 100 = 58.75 → 58.8
    expected_pct = round(
        (tank_height_mm - _TD_GOOD_SIGNAL_AIR_GAP_MM) / tank_height_mm * 100, 1
    )
    fill_sensor = hass.states.get("sensor.td40_td200_7510_tank_fill")
    assert fill_sensor is not None
    assert float(fill_sensor.state) == expected_pct

    medium_type_sensor = hass.states.get("sensor.td40_td200_7510_medium_type")
    assert medium_type_sensor is not None
    assert medium_type_sensor.state == MediumType.AIR.value

    # No propane_preset sensor for AIR medium
    assert hass.states.get("sensor.td40_td200_7510_propane_preset") is None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_top_mount_empty_tank(hass: HomeAssistant) -> None:
    """Test fill% clamps to 0% when air gap equals or exceeds tank height."""
    tank_height_mm = 100
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:75:10",
        data={
            CONF_MEDIUM_TYPE: MediumType.AIR.value,
            CONF_TANK_SIZE: TankSize.CUSTOM,
            CONF_CUSTOM_TANK_HEIGHT: tank_height_mm,
            CONF_TOP_MOUNT: True,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # TD_GOOD_SIGNAL reports 165 mm air gap — greater than tank height of 100 mm.
    # fill% would be negative; clamped to 0.0.
    inject_bluetooth_service_info(hass, TD_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()

    fill_sensor = hass.states.get("sensor.td40_td200_7510_tank_fill")
    assert fill_sensor is not None
    assert float(fill_sensor.state) == 0.0

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_top_mount_no_fill_percent_when_height_zero(
    hass: HomeAssistant,
) -> None:
    """Test no fill% sensor when custom_tank_height is 0 (user opted out)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:75:10",
        data={
            CONF_MEDIUM_TYPE: MediumType.AIR.value,
            CONF_TANK_SIZE: TankSize.CUSTOM,
            CONF_CUSTOM_TANK_HEIGHT: 0,
            CONF_TOP_MOUNT: True,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, TD_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.td40_td200_7510_tank_fill") is None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_top_mount_full_tank(hass: HomeAssistant) -> None:
    """Test fill% is 100% when air gap is 0 (tank completely full).

    TD_SERVICE_INFO reports level=0 mm (air gap = 0), meaning the liquid is
    right at the sensor — tank is full.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:75:10",
        data={
            CONF_MEDIUM_TYPE: MediumType.AIR.value,
            CONF_TANK_SIZE: TankSize.CUSTOM,
            CONF_CUSTOM_TANK_HEIGHT: 400,
            CONF_TOP_MOUNT: True,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # TD_SERVICE_INFO: reading_quality=1, level=0 mm
    inject_bluetooth_service_info(hass, TD_SERVICE_INFO)
    await hass.async_block_till_done()

    fill_sensor = hass.states.get("sensor.td40_td200_7510_tank_fill")
    assert fill_sensor is not None
    assert float(fill_sensor.state) == 100.0

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


# ---------------------------------------------------------------------------
# IBC tote preset sensor tests
# ---------------------------------------------------------------------------

# For fresh water + PRO_GOOD_SIGNAL_SERVICE_INFO the library yields 711 mm.
_FRESH_WATER_LEVEL_MM = 711


async def test_sensors_ibc_275_bottom_mount(hass: HomeAssistant) -> None:
    """Test fill % for a 275 gal IBC tote with a bottom-mount sensor (fresh water).

    empty=38.1 mm, full=980.0 mm; level=711 mm.
    Expected: (711 - 38.1) / (980.0 - 38.1) * 100 = 71.4%.
    """
    empty_mm, full_mm = IBC_TANK_SIZE_RANGES[TankSize.IBC_275]
    expected_pct = round(
        (_FRESH_WATER_LEVEL_MM - empty_mm) / (full_mm - empty_mm) * 100, 1
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_MEDIUM_TYPE: MediumType.FRESH_WATER.value,
            CONF_TANK_SIZE: TankSize.IBC_275,
            CONF_CUSTOM_TANK_HEIGHT: 0,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    # 4 base + medium_type + tank_fill = 6 sensors
    assert len(hass.states.async_all("sensor")) == 7

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    assert float(pct_sensor.state) == expected_pct

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_ibc_330_bottom_mount(hass: HomeAssistant) -> None:
    """Test fill % for a 330 gal IBC tote with a bottom-mount sensor (fresh water).

    empty=38.1 mm, full=1140.0 mm; level=711 mm.
    Expected: (711 - 38.1) / (1140.0 - 38.1) * 100 ≈ 61.1%.
    """
    empty_mm, full_mm = IBC_TANK_SIZE_RANGES[TankSize.IBC_330]
    expected_pct = round(
        (_FRESH_WATER_LEVEL_MM - empty_mm) / (full_mm - empty_mm) * 100, 1
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_MEDIUM_TYPE: MediumType.FRESH_WATER.value,
            CONF_TANK_SIZE: TankSize.IBC_330,
            CONF_CUSTOM_TANK_HEIGHT: 0,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    assert float(pct_sensor.state) == expected_pct

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_ibc_275_top_mount(hass: HomeAssistant) -> None:
    """Test fill % inversion for a 275 gal IBC tote with a top-mount sensor.

    Inverted range: empty_mm=980.0, full_mm=0.0.
    Air gap reading = 165 mm (TD_GOOD_SIGNAL_SERVICE_INFO).
    Expected: (165 - 980.0) / (0.0 - 980.0) * 100 = 83.2%.
    """
    _, full_mm = IBC_TANK_SIZE_RANGES[TankSize.IBC_275]
    expected_pct = round(
        (_TD_GOOD_SIGNAL_AIR_GAP_MM - full_mm) / (0.0 - full_mm) * 100, 1
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:75:10",
        data={
            CONF_MEDIUM_TYPE: MediumType.AIR.value,
            CONF_TANK_SIZE: TankSize.IBC_275,
            CONF_CUSTOM_TANK_HEIGHT: 0,
            CONF_TOP_MOUNT: True,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, TD_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()

    fill_sensor = hass.states.get("sensor.td40_td200_7510_tank_fill")
    assert fill_sensor is not None
    assert float(fill_sensor.state) == expected_pct

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_ibc_330_top_mount(hass: HomeAssistant) -> None:
    """Test fill % inversion for a 330 gal IBC tote with a top-mount sensor.

    Inverted range: empty_mm=1140.0, full_mm=0.0.
    Air gap reading = 165 mm (TD_GOOD_SIGNAL_SERVICE_INFO).
    Expected: (165 - 1140.0) / (0.0 - 1140.0) * 100 = 85.5%.
    """
    _, full_mm = IBC_TANK_SIZE_RANGES[TankSize.IBC_330]
    expected_pct = round(
        (_TD_GOOD_SIGNAL_AIR_GAP_MM - full_mm) / (0.0 - full_mm) * 100, 1
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:75:10",
        data={
            CONF_MEDIUM_TYPE: MediumType.AIR.value,
            CONF_TANK_SIZE: TankSize.IBC_330,
            CONF_CUSTOM_TANK_HEIGHT: 0,
            CONF_TOP_MOUNT: True,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, TD_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()

    fill_sensor = hass.states.get("sensor.td40_td200_7510_tank_fill")
    assert fill_sensor is not None
    assert float(fill_sensor.state) == expected_pct

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_ibc_preset_not_used_for_propane(hass: HomeAssistant) -> None:
    """Test that IBC presets work independently of propane acoustic coefficients.

    An IBC tote selected with a propane medium type should still produce a fill %
    using the IBC dimensions (since IBC ranges are checked before the propane guard).
    In practice the UI prevents propane + IBC, but the sensor layer should handle it.
    """
    _, full_mm = IBC_TANK_SIZE_RANGES[TankSize.IBC_275]
    # Propane + PRO_GOOD_SIGNAL → level = 341 mm
    expected_pct = round(
        (_GOOD_SIGNAL_LEVEL_MM - TANK_EMPTY_MM) / (full_mm - TANK_EMPTY_MM) * 100, 1
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_MEDIUM_TYPE: MediumType.PROPANE.value,
            CONF_TANK_SIZE: TankSize.IBC_275,
            CONF_CUSTOM_TANK_HEIGHT: 0,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()

    pct_sensor = hass.states.get("sensor.pro_plus_eeff_tank_fill")
    assert pct_sensor is not None
    assert float(pct_sensor.state) == expected_pct

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


# ---------------------------------------------------------------------------
# Tank volume sensor tests
# ---------------------------------------------------------------------------


async def test_sensors_volume_sensor_preset_tank(hass: HomeAssistant) -> None:
    """Test that a volume sensor is created for a preset tank.

    LB_20 capacity = 4.7 gal; fill = 100% (level exceeds full); volume = 4.7 gal.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_TANK_SIZE: TankSize.LB_20},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()

    vol_sensor = hass.states.get("sensor.pro_plus_eeff_tank_volume")
    assert vol_sensor is not None
    assert float(vol_sensor.state) == round(
        1.0 * TANK_SIZE_CAPACITIES[TankSize.LB_20], 2
    )
    assert vol_sensor.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfVolume.GALLONS
    assert vol_sensor.attributes[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_volume_sensor_custom_with_capacity(hass: HomeAssistant) -> None:
    """Test that a volume sensor is created for a custom tank with capacity configured.

    Height=682 mm, level=341 mm → fill=50.0%; capacity=20.0 gal → volume=10.0 gal.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_TANK_SIZE: TankSize.CUSTOM,
            CONF_CUSTOM_TANK_HEIGHT: 682,
            CONF_TANK_CAPACITY: 20.0,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    # 4 base + tank_fill + tank_volume = 6
    assert len(hass.states.async_all("sensor")) == 6

    vol_sensor = hass.states.get("sensor.pro_plus_eeff_tank_volume")
    assert vol_sensor is not None
    assert float(vol_sensor.state) == 10.0
    assert vol_sensor.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfVolume.GALLONS

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_volume_sensor_custom_no_capacity(hass: HomeAssistant) -> None:
    """Test that no volume sensor is created when custom tank capacity is 0."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_TANK_SIZE: TankSize.CUSTOM,
            CONF_CUSTOM_TANK_HEIGHT: 682,
            CONF_TANK_CAPACITY: 0.0,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_GOOD_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.pro_plus_eeff_tank_volume") is None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_volume_sensor_unusable_signal(hass: HomeAssistant) -> None:
    """Test that volume sensor is created but unknown when signal is unusable."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={CONF_TANK_SIZE: TankSize.LB_20},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info(hass, PRO_UNUSABLE_SIGNAL_SERVICE_INFO)
    await hass.async_block_till_done()

    vol_sensor = hass.states.get("sensor.pro_plus_eeff_tank_volume")
    assert vol_sensor is not None
    assert vol_sensor.state == STATE_UNKNOWN

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
