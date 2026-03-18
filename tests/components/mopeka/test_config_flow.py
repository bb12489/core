"""Test the Mopeka config flow."""

from unittest.mock import patch

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.mopeka.const import (
    CONF_CUSTOM_TANK_HEIGHT,
    CONF_MEDIUM_TYPE,
    CONF_TANK_SIZE,
    DOMAIN,
    MediumType,
    TankSize,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import NOT_MOPEKA_SERVICE_INFO, PRO_SERVICE_INFO

from tests.common import MockConfigEntry

# ---------------------------------------------------------------------------
# Bluetooth discovery flow
# ---------------------------------------------------------------------------


async def test_async_step_bluetooth_valid_device(hass: HomeAssistant) -> None:
    """Test discovery via bluetooth with a valid propane device — preset flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=PRO_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    # Step 1: select medium type (propane)
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_MEDIUM_TYPE: MediumType.PROPANE.value},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "tank_config"

    # Step 2: select tank preset
    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_TANK_SIZE: TankSize.LB_20},
        )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Pro Plus EEFF"
    assert result3["data"] == {
        CONF_MEDIUM_TYPE: MediumType.PROPANE.value,
        CONF_TANK_SIZE: TankSize.LB_20,
        CONF_CUSTOM_TANK_HEIGHT: 0,
    }
    assert result3["result"].unique_id == "aa:bb:cc:dd:ee:ff"


async def test_async_step_bluetooth_valid_device_custom_tank(
    hass: HomeAssistant,
) -> None:
    """Test BT discovery with custom tank height — three-step flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=PRO_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    # Step 1: propane
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_MEDIUM_TYPE: MediumType.PROPANE.value},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "tank_config"

    # Step 2: select Custom
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_TANK_SIZE: TankSize.CUSTOM},
    )
    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "custom_height"

    # Step 3: enter custom height
    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        result4 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CUSTOM_TANK_HEIGHT: 500},
        )
    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert result4["data"][CONF_TANK_SIZE] == TankSize.CUSTOM
    assert result4["data"][CONF_CUSTOM_TANK_HEIGHT] == 500
    assert result4["result"].unique_id == "aa:bb:cc:dd:ee:ff"


async def test_async_step_bluetooth_non_propane(hass: HomeAssistant) -> None:
    """Test BT discovery with a non-propane medium — goes straight to custom height."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=PRO_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    # Step 1: non-propane medium
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_MEDIUM_TYPE: MediumType.FRESH_WATER.value},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "custom_height"

    # Step 2: enter custom height
    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CUSTOM_TANK_HEIGHT: 600},
        )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["data"][CONF_MEDIUM_TYPE] == MediumType.FRESH_WATER.value
    assert result3["data"][CONF_TANK_SIZE] == TankSize.CUSTOM
    assert result3["data"][CONF_CUSTOM_TANK_HEIGHT] == 600


async def test_async_step_bluetooth_not_mopeka(hass: HomeAssistant) -> None:
    """Test discovery via bluetooth not mopeka."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=NOT_MOPEKA_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_supported"


# ---------------------------------------------------------------------------
# User (manual) flow
# ---------------------------------------------------------------------------


async def test_async_step_user_no_devices_found(hass: HomeAssistant) -> None:
    """Test setup from service info cache with no devices found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_async_step_user_with_found_devices(hass: HomeAssistant) -> None:
    """Test setup from service info cache with devices found — propane preset flow."""
    with patch(
        "homeassistant.components.mopeka.config_flow.async_discovered_service_info",
        return_value=[PRO_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Step 1: address + medium type (propane)
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "address": "aa:bb:cc:dd:ee:ff",
            CONF_MEDIUM_TYPE: MediumType.PROPANE.value,
        },
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "tank_config"

    # Step 2: tank preset
    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_TANK_SIZE: TankSize.LB_40},
        )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Pro Plus EEFF"
    assert result3["data"][CONF_MEDIUM_TYPE] == MediumType.PROPANE.value
    assert result3["data"][CONF_TANK_SIZE] == TankSize.LB_40
    assert result3["result"].unique_id == "aa:bb:cc:dd:ee:ff"


async def test_async_step_user_non_propane(hass: HomeAssistant) -> None:
    """Test user flow with a non-propane medium — goes straight to custom height."""
    with patch(
        "homeassistant.components.mopeka.config_flow.async_discovered_service_info",
        return_value=[PRO_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] is FlowResultType.FORM

    # Step 1: diesel (non-propane)
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "address": "aa:bb:cc:dd:ee:ff",
            CONF_MEDIUM_TYPE: MediumType.DIESEL.value,
        },
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "custom_height"

    # Step 2: enter custom height
    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CUSTOM_TANK_HEIGHT: 600},
        )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["data"][CONF_MEDIUM_TYPE] == MediumType.DIESEL.value
    assert result3["data"][CONF_TANK_SIZE] == TankSize.CUSTOM
    assert result3["data"][CONF_CUSTOM_TANK_HEIGHT] == 600


async def test_async_step_user_replace_ignored(hass: HomeAssistant) -> None:
    """Test setup from service info can replace an ignored entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=PRO_SERVICE_INFO.address,
        data={},
        source=config_entries.SOURCE_IGNORE,
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.mopeka.config_flow.async_discovered_service_info",
        return_value=[PRO_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "address": "aa:bb:cc:dd:ee:ff",
            CONF_MEDIUM_TYPE: MediumType.PROPANE.value,
        },
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "tank_config"

    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_TANK_SIZE: TankSize.LB_20},
        )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Pro Plus EEFF"
    assert result3["data"][CONF_MEDIUM_TYPE] == MediumType.PROPANE.value
    assert result3["result"].unique_id == "aa:bb:cc:dd:ee:ff"


async def test_async_step_user_device_added_between_steps(
    hass: HomeAssistant,
) -> None:
    """Test the device gets added via another flow between the two user-flow steps."""
    with patch(
        "homeassistant.components.mopeka.config_flow.async_discovered_service_info",
        return_value=[PRO_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Step 1 succeeds — flow advances to tank_config
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "address": "aa:bb:cc:dd:ee:ff",
            CONF_MEDIUM_TYPE: MediumType.PROPANE.value,
        },
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "tank_config"

    # Another flow adds the same device before step 2 is submitted
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_TANK_SIZE: TankSize.LB_20},
        )
    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "already_configured"


async def test_async_step_user_with_found_devices_already_setup(
    hass: HomeAssistant,
) -> None:
    """Test setup from service info cache with devices found but already set up."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.mopeka.config_flow.async_discovered_service_info",
        return_value=[PRO_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_async_step_bluetooth_devices_already_setup(hass: HomeAssistant) -> None:
    """Test we can't start a flow if there is already a config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=PRO_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_async_step_bluetooth_already_in_progress(hass: HomeAssistant) -> None:
    """Test we can't start a flow for the same device twice."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=PRO_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=PRO_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_in_progress"


async def test_async_step_user_takes_precedence_over_discovery(
    hass: HomeAssistant,
) -> None:
    """Test manual setup takes precedence over discovery."""
    result_bt = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=PRO_SERVICE_INFO,
    )
    assert result_bt["type"] is FlowResultType.FORM
    assert result_bt["step_id"] == "bluetooth_confirm"

    with patch(
        "homeassistant.components.mopeka.config_flow.async_discovered_service_info",
        return_value=[PRO_SERVICE_INFO],
    ):
        result_user = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        assert result_user["type"] is FlowResultType.FORM

    # User step 1: address + medium type
    result_user2 = await hass.config_entries.flow.async_configure(
        result_user["flow_id"],
        user_input={
            "address": "aa:bb:cc:dd:ee:ff",
            CONF_MEDIUM_TYPE: MediumType.PROPANE.value,
        },
    )
    assert result_user2["type"] is FlowResultType.FORM
    assert result_user2["step_id"] == "tank_config"

    # User step 2: tank config — creates entry and aborts the BT flow
    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        result_user3 = await hass.config_entries.flow.async_configure(
            result_user["flow_id"],
            user_input={CONF_TANK_SIZE: TankSize.LB_20},
        )
    assert result_user3["type"] is FlowResultType.CREATE_ENTRY
    assert result_user3["title"] == "Pro Plus EEFF"
    assert result_user3["data"][CONF_MEDIUM_TYPE] == MediumType.PROPANE.value
    assert result_user3["result"].unique_id == "aa:bb:cc:dd:ee:ff"

    # Original BT flow must be aborted
    assert not hass.config_entries.flow.async_progress(DOMAIN)


# ---------------------------------------------------------------------------
# Options flow
# ---------------------------------------------------------------------------


async def test_async_step_reconfigure_options(hass: HomeAssistant) -> None:
    """Test reconfig options: change medium type — two-step options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:75:10",
        title="TD40/TD200 7510",
        data={
            CONF_MEDIUM_TYPE: MediumType.AIR.value,
            CONF_TANK_SIZE: TankSize.LB_20,
            CONF_CUSTOM_TANK_HEIGHT: 0,
        },
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.data[CONF_MEDIUM_TYPE] == MediumType.AIR.value

    # Open options flow — step 1: medium type pre-filled from config
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    schema: vol.Schema = result["data_schema"]
    medium_type_key = next(
        iter(key for key in schema.schema if key == CONF_MEDIUM_TYPE)
    )
    assert medium_type_key.default() == MediumType.AIR.value

    # Step 1: switch to fresh water (non-propane)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_MEDIUM_TYPE: MediumType.FRESH_WATER.value},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "custom_height"

    # Step 2: enter custom height
    result3 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_CUSTOM_TANK_HEIGHT: 400},
    )
    assert result3["type"] is FlowResultType.CREATE_ENTRY

    assert entry.data[CONF_MEDIUM_TYPE] == MediumType.FRESH_WATER.value
    assert entry.data[CONF_TANK_SIZE] == TankSize.CUSTOM
    assert entry.data[CONF_CUSTOM_TANK_HEIGHT] == 400


async def test_options_propane_flow(hass: HomeAssistant) -> None:
    """Test options flow for a propane entry — preset selector shown in step 2."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_MEDIUM_TYPE: MediumType.PROPANE.value,
            CONF_TANK_SIZE: TankSize.LB_20,
            CONF_CUSTOM_TANK_HEIGHT: 0,
        },
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    # Step 1: keep propane
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_MEDIUM_TYPE: MediumType.PROPANE.value},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "tank_config"

    # Propane: preset selector present, pre-filled with existing value
    schema: vol.Schema = result2["data_schema"]
    assert CONF_TANK_SIZE in schema.schema
    tank_size_key = next(iter(key for key in schema.schema if key == CONF_TANK_SIZE))
    assert tank_size_key.default() == TankSize.LB_20

    # Step 2: change to 100 lb
    result3 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_TANK_SIZE: TankSize.LB_100},
    )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert entry.data[CONF_TANK_SIZE] == TankSize.LB_100


async def test_options_propane_custom_flow(hass: HomeAssistant) -> None:
    """Test options flow: propane → Custom → custom height page."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_MEDIUM_TYPE: MediumType.PROPANE.value,
            CONF_TANK_SIZE: TankSize.LB_20,
            CONF_CUSTOM_TANK_HEIGHT: 0,
        },
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["step_id"] == "init"

    # Step 1: keep propane
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_MEDIUM_TYPE: MediumType.PROPANE.value},
    )
    assert result2["step_id"] == "tank_config"

    # Step 2: select Custom → redirects to custom_height page
    result3 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_TANK_SIZE: TankSize.CUSTOM},
    )
    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "custom_height"

    # Step 3: enter custom height
    result4 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_CUSTOM_TANK_HEIGHT: 750},
    )
    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert entry.data[CONF_TANK_SIZE] == TankSize.CUSTOM
    assert entry.data[CONF_CUSTOM_TANK_HEIGHT] == 750


# ---------------------------------------------------------------------------
# Reconfigure flow
# ---------------------------------------------------------------------------


async def test_reconfigure_flow_propane(hass: HomeAssistant) -> None:
    """Test reconfigure flow for a propane entry — medium type and tank size."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_MEDIUM_TYPE: MediumType.PROPANE.value,
            CONF_TANK_SIZE: TankSize.LB_20,
            CONF_CUSTOM_TANK_HEIGHT: 0,
        },
    )
    entry.add_to_hass(hass)

    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await entry.start_reconfigure_flow(hass)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

        # Step 1: keep propane
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_MEDIUM_TYPE: MediumType.PROPANE.value},
        )
        assert result2["type"] is FlowResultType.FORM
        assert result2["step_id"] == "reconfigure_tank_config"

        # Propane: preset selector present, pre-filled with existing value
        schema: vol.Schema = result2["data_schema"]
        assert CONF_TANK_SIZE in schema.schema
        tank_size_key = next(
            iter(key for key in schema.schema if key == CONF_TANK_SIZE)
        )
        assert tank_size_key.default() == TankSize.LB_20

        # Step 2: change to 40 lb
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_TANK_SIZE: TankSize.LB_40},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reconfigure_successful"
    assert entry.data[CONF_MEDIUM_TYPE] == MediumType.PROPANE.value
    assert entry.data[CONF_TANK_SIZE] == TankSize.LB_40
    assert entry.data[CONF_CUSTOM_TANK_HEIGHT] == 0


async def test_reconfigure_flow_propane_custom(hass: HomeAssistant) -> None:
    """Test reconfigure flow: propane → Custom → custom height page."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_MEDIUM_TYPE: MediumType.PROPANE.value,
            CONF_TANK_SIZE: TankSize.LB_20,
            CONF_CUSTOM_TANK_HEIGHT: 0,
        },
    )
    entry.add_to_hass(hass)

    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await entry.start_reconfigure_flow(hass)
        assert result["step_id"] == "reconfigure"

        # Step 1: keep propane
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_MEDIUM_TYPE: MediumType.PROPANE.value},
        )
        assert result2["step_id"] == "reconfigure_tank_config"

        # Step 2: select Custom → redirects to custom height page
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_TANK_SIZE: TankSize.CUSTOM},
        )
        assert result3["type"] is FlowResultType.FORM
        assert result3["step_id"] == "reconfigure_custom_height"

        # Step 3: enter custom height
        result4 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CUSTOM_TANK_HEIGHT: 900},
        )
        await hass.async_block_till_done()

    assert result4["type"] is FlowResultType.ABORT
    assert result4["reason"] == "reconfigure_successful"
    assert entry.data[CONF_TANK_SIZE] == TankSize.CUSTOM
    assert entry.data[CONF_CUSTOM_TANK_HEIGHT] == 900


async def test_reconfigure_flow_non_propane(hass: HomeAssistant) -> None:
    """Test reconfigure flow switching to a non-propane medium — custom height page."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_MEDIUM_TYPE: MediumType.PROPANE.value,
            CONF_TANK_SIZE: TankSize.LB_20,
            CONF_CUSTOM_TANK_HEIGHT: 0,
        },
    )
    entry.add_to_hass(hass)

    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await entry.start_reconfigure_flow(hass)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

        # Step 1: switch to fresh water
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_MEDIUM_TYPE: MediumType.FRESH_WATER.value},
        )
        assert result2["type"] is FlowResultType.FORM
        assert result2["step_id"] == "reconfigure_custom_height"

        # Step 2: enter custom height
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CUSTOM_TANK_HEIGHT: 350},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reconfigure_successful"
    assert entry.data[CONF_MEDIUM_TYPE] == MediumType.FRESH_WATER.value
    assert entry.data[CONF_TANK_SIZE] == TankSize.CUSTOM
    assert entry.data[CONF_CUSTOM_TANK_HEIGHT] == 350
