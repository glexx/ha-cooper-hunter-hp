"""Integration tests against a fake Modbus slave serving a real register snapshot."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from custom_components.cooper_hunter_hp.const import (
    CONF_ENTITY_PREFIX,
    CONF_MODEL,
    CONF_SLAVE,
    CONF_TRANSPORT,
    DOMAIN,
)
from custom_components.cooper_hunter_hp.coordinator import controller_time, decode, encode
from custom_components.cooper_hunter_hp.modbus_client import ModbusClient, ModbusError, crc16
from custom_components.cooper_hunter_hp.sensor import active_faults

from .conftest import SNAPSHOT


async def _setup(hass: HomeAssistant, fake_slave, enable_all: bool = False) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Heat pump",
        unique_id=f"127.0.0.1:{fake_slave.port}:1",
        data={
            CONF_TRANSPORT: "tcp",
            CONF_HOST: "127.0.0.1",
            CONF_PORT: fake_slave.port,
            CONF_SLAVE: 1,
            CONF_MODEL: "CH-HP15UIMPZM",
            CONF_ENTITY_PREFIX: "hp",
        },
    )
    entry.add_to_hass(hass)
    with patch("custom_components.cooper_hunter_hp.coordinator.WRITE_SETTLE_DELAY", 0):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


def t(addr: int) -> float:
    return round(decode(SNAPSHOT, addr, "temp"), 1)


async def test_config_flow(hass: HomeAssistant, fake_slave) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_TRANSPORT: "tcp"})
    assert result["step_id"] == "network"
    with patch("custom_components.cooper_hunter_hp.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "127.0.0.1", CONF_PORT: fake_slave.port, CONF_NAME: "Тепловий насос",
             CONF_MODEL: "CH-HP15UIMPZM", CONF_SLAVE: 1, CONF_ENTITY_PREFIX: "HP"},
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Тепловий насос"
    assert result["data"][CONF_ENTITY_PREFIX] == "hp"


async def test_config_flow_cannot_connect(hass: HomeAssistant, fake_slave) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_TRANSPORT: "tcp"})
    with patch("custom_components.cooper_hunter_hp.modbus_client.ModbusClient._execute",
               side_effect=ModbusError("boom")):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "127.0.0.1", CONF_PORT: fake_slave.port, CONF_NAME: "x",
             CONF_MODEL: "m", CONF_SLAVE: 1, CONF_ENTITY_PREFIX: "hp"},
        )
    assert result["errors"] == {"base": "cannot_connect"}


async def test_states(hass: HomeAssistant, fake_slave) -> None:
    await _setup(hass, fake_slave)
    assert float(hass.states.get("sensor.hp_water_inlet_temperature").state) == t(2045)
    assert float(hass.states.get("sensor.hp_dhw_tank_temperature").state) == t(2047)
    assert float(hass.states.get("sensor.hp_outdoor_temperature").state) == t(2048)
    assert hass.states.get("sensor.hp_operating_state").state == "heating"
    assert hass.states.get("select.hp_operating_mode").state == "dhw_heating"
    assert hass.states.get("switch.hp_power").state == "on"
    assert hass.states.get("binary_sensor.hp_fault").state == "off"
    assert hass.states.get("sensor.hp_active_faults").state == "0"
    assert hass.states.get("sensor.hp_firmware").state.startswith("WF")
    assert int(hass.states.get("sensor.hp_energy_consumption").state) == (SNAPSHOT[2078] << 16) | SNAPSHOT[2079]

    dhw = hass.states.get("number.hp_dhw_setpoint")
    assert float(dhw.state) == t(1157)
    assert dhw.attributes["min"] == t(1176)
    assert dhw.attributes["max"] == t(1177)

    climate = hass.states.get("climate.hp_heating")
    assert climate.state == "heat"
    assert climate.attributes["temperature"] == t(1158)
    assert climate.attributes["current_temperature"] == t(2052)  # 1035 = buffer tank
    assert "cool" in climate.attributes["hvac_modes"]

    wh = hass.states.get("water_heater.hp_dhw")
    assert wh.state == "heat_pump"
    assert wh.attributes["temperature"] == t(1157)
    assert wh.attributes["current_temperature"] == t(2047)

    # Disabled-by-default entities exist in the registry but have no state.
    registry = er.async_get(hass)
    assert registry.async_get("sensor.hp_cop").disabled
    assert hass.states.get("sensor.hp_cop") is None


async def test_number_write(hass: HomeAssistant, fake_slave) -> None:
    await _setup(hass, fake_slave)
    with patch("custom_components.cooper_hunter_hp.coordinator.WRITE_SETTLE_DELAY", 0):
        await hass.services.async_call("number", "set_value",
                                       {"entity_id": "number.hp_dhw_setpoint", "value": 52.5}, blocking=True)
        await hass.services.async_call("number", "set_value",
                                       {"entity_id": "number.hp_curve_slope", "value": 1.3}, blocking=True)
    assert (1157, 525) in fake_slave.writes
    assert (1234, 13) in fake_slave.writes
    assert float(hass.states.get("number.hp_dhw_setpoint").state) == 52.5


async def test_climate_and_water_heater_modes(hass: HomeAssistant, fake_slave) -> None:
    await _setup(hass, fake_slave)
    with patch("custom_components.cooper_hunter_hp.coordinator.WRITE_SETTLE_DELAY", 0):
        # DHW+heating -> climate off keeps DHW running
        await hass.services.async_call("climate", "set_hvac_mode",
                                       {"entity_id": "climate.hp_heating", "hvac_mode": "off"}, blocking=True)
        assert fake_slave.registers[1012] == 0 and fake_slave.registers[1011] == 1
        assert hass.states.get("climate.hp_heating").state == "off"
        assert hass.states.get("water_heater.hp_dhw").state == "heat_pump"
        # DHW only -> water heater off => whole unit off
        await hass.services.async_call("water_heater", "set_operation_mode",
                                       {"entity_id": "water_heater.hp_dhw", "operation_mode": "off"},
                                       blocking=True)
        assert fake_slave.registers[1011] == 0
        # unit off -> heating on => heating only, power on
        await hass.services.async_call("climate", "set_hvac_mode",
                                       {"entity_id": "climate.hp_heating", "hvac_mode": "heat"}, blocking=True)
        assert fake_slave.registers[1012] == 1 and fake_slave.registers[1011] == 1
        # add DHW -> DHW+heating
        await hass.services.async_call("water_heater", "set_operation_mode",
                                       {"entity_id": "water_heater.hp_dhw", "operation_mode": "heat_pump"},
                                       blocking=True)
        assert fake_slave.registers[1012] == 3
        # cooling setpoint is used in cool mode
        await hass.services.async_call("climate", "set_temperature",
                                       {"entity_id": "climate.hp_heating", "hvac_mode": "cool",
                                        "temperature": 18}, blocking=True)
        assert fake_slave.registers[1012] == 4
        assert fake_slave.registers[1159] == 180
        await hass.services.async_call("select", "select_option",
                                       {"entity_id": "select.hp_operating_mode", "option": "heating"},
                                       blocking=True)
        assert fake_slave.registers[1012] == 1


async def test_clock_sync(hass: HomeAssistant, fake_slave) -> None:
    # The snapshot has the controller RTC disabled (scheduled disinfection can never
    # fire in that state) -> the integration syncs it on the first parameter poll.
    assert SNAPSHOT[1250] == 0
    await _setup(hass, fake_slave)
    assert (1250, 1) in fake_slave.writes
    synced = controller_time(fake_slave.registers, dt_util.DEFAULT_TIME_ZONE)
    assert synced is not None
    assert abs(dt_util.now() - synced) < timedelta(minutes=2)
    assert hass.states.get("sensor.hp_controller_time").state not in ("unknown", "unavailable")


async def test_clock_resync_on_drift(hass: HomeAssistant, fake_slave) -> None:
    entry = await _setup(hass, fake_slave)
    coordinator = entry.runtime_data
    fake_slave.writes.clear()
    # In sync -> no write on the next parameter poll.
    coordinator._params_dirty = True
    await coordinator.async_refresh()
    assert not any(a == 1250 for a, _ in fake_slave.writes)
    # Drift beyond the tolerance -> re-synced.
    fake_slave.registers[1252] = (fake_slave.registers[1252] + 3) % 24
    coordinator._params_dirty = True
    await coordinator.async_refresh()
    assert (1250, 1) in fake_slave.writes


async def test_polls_only_answered_pages(hass: HomeAssistant, fake_slave) -> None:
    # The controller silently ignores reads outside its pages (e.g. 1271+), which costs
    # a full timeout + retries on a shared gateway; the integration must never issue them.
    entry = await _setup(hass, fake_slave)
    coordinator = entry.runtime_data
    coordinator._params_dirty = True
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert fake_slave.unanswered == []
    assert hass.states.get("switch.hp_disinfection_in_standby") is None


async def test_fault_bits(hass: HomeAssistant, fake_slave) -> None:
    fake_slave.registers[2085] = 1 << 8  # water flow protection
    fake_slave.registers[2090] = 1 << 3  # undocumented bit
    await _setup(hass, fake_slave)
    assert hass.states.get("binary_sensor.hp_water_flow_protection").state == "on"
    assert hass.states.get("binary_sensor.hp_fault").state == "on"
    faults = hass.states.get("sensor.hp_active_faults")
    assert faults.state == "2"
    assert faults.attributes["faults"] == ["water_flow_protection", "fault_2090_bit3"]


async def test_poll_failure_tolerance(hass: HomeAssistant, fake_slave) -> None:
    entry = await _setup(hass, fake_slave)
    coordinator = entry.runtime_data
    with patch.object(coordinator.client, "read_holding_registers", side_effect=ModbusError("x")):
        await coordinator.async_refresh()
        assert coordinator.last_update_success  # stale data tolerated
        for _ in range(3):
            await coordinator.async_refresh()
        assert not coordinator.last_update_success
    await coordinator.async_refresh()
    assert coordinator.last_update_success


async def test_client_rejects_wrong_page(fake_slave) -> None:
    client = ModbusClient("tcp", host="127.0.0.1", port=fake_slave.port, timeout=0.5, retries=0)
    values = await client.read_holding_registers(1, 2001, 10)
    assert values[9] == 2001
    with pytest.raises(ModbusError):
        await client.read_holding_registers(1, 3001, 10)  # unsupported -> no answer
    await client.close()


def test_codec() -> None:
    assert decode({1: 65286}, 1, "temp") == -25.0
    assert decode({1: 32767}, 1, "temp") is None
    assert decode({1: 1, 2: 2}, 1, "u32") == 65538
    assert encode(-25.0, "temp") == 65286
    assert encode(1.3, "d5") == 13
    assert crc16(bytes.fromhex("010300000001")) == bytes.fromhex("840a")


def test_active_faults_known_and_unknown() -> None:
    assert active_faults({2081: 1}) [0][0] == "ipm_overcurrent_fault"
    assert active_faults({}) == []


async def test_write_dropped_echo_applied(fake_slave) -> None:
    """Controller applies the write but never echoes: read-back confirms, sent once."""
    fake_slave.write_mode = "drop_echo"
    client = ModbusClient("tcp", host="127.0.0.1", port=fake_slave.port, timeout=0.5, retries=3)
    await client.write_register(1, 1157, 500)
    assert fake_slave.writes == [(1157, 500)]
    assert fake_slave.registers[1157] == 500
    await client.close()


async def test_write_dropped_echo_not_applied(fake_slave) -> None:
    """No echo and the register did not change: the write must fail."""
    fake_slave.write_mode = "ignore_write"
    before = fake_slave.registers[1157]
    client = ModbusClient("tcp", host="127.0.0.1", port=fake_slave.port, timeout=0.5, retries=3)
    with pytest.raises(ModbusError):
        await client.write_register(1, 1157, 500)
    assert fake_slave.writes == []
    assert fake_slave.registers[1157] == before
    await client.close()


async def test_write_clamped_echo_warns(fake_slave, caplog) -> None:
    """An echo with a different value is accepted but logged as a warning."""
    fake_slave.write_mode = "clamp"
    client = ModbusClient("tcp", host="127.0.0.1", port=fake_slave.port, timeout=0.5, retries=0)
    await client.write_register(1, 1157, 999)
    assert "requested 999 but controller stored 600" in caplog.text
    await client.close()
