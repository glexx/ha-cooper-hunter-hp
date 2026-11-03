"""Sensors for the Cooper&Hunter heat pump."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import HeatPumpConfigEntry
from .coordinator import HeatPumpCoordinator, controller_time
from .entity import HeatPumpEntity
from .registers import (
    DERIVED_SENSORS,
    FAULT_BITS,
    FAULT_REGISTERS,
    REG_FLOW,
    REG_INLET,
    REG_OUTLET,
    SENSORS,
    Base,
    SensorDef,
)

# Specific heat of water × density, kWh/(m³·K)
WATER_HEAT_CAPACITY = 1.163


async def async_setup_entry(
    hass: HomeAssistant, entry: HeatPumpConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [RegisterSensor(coordinator, d) for d in SENSORS]
    derived = {d.key: d for d in DERIVED_SENSORS}
    entities += [
        DeltaTSensor(coordinator, derived["water_delta_t"]),
        ThermalPowerSensor(coordinator, derived["thermal_power"]),
        ActiveFaultsSensor(coordinator, derived["active_faults"]),
        FirmwareSensor(coordinator, derived["firmware"]),
        ControllerTimeSensor(coordinator, derived["controller_time"]),
    ]
    async_add_entities(entities)


class RegisterSensor(HeatPumpEntity, SensorEntity):
    definition: SensorDef

    def __init__(self, coordinator: HeatPumpCoordinator, definition: SensorDef) -> None:
        super().__init__(coordinator, "sensor", definition)
        self._attr_native_unit_of_measurement = definition.unit
        if definition.device_class:
            self._attr_device_class = SensorDeviceClass(definition.device_class)
        if definition.state_class:
            self._attr_state_class = SensorStateClass(definition.state_class)
        if definition.precision is not None:
            self._attr_suggested_display_precision = definition.precision
        elif definition.dtype == "temp":
            self._attr_suggested_display_precision = 1
        if definition.options:
            self._attr_options = [o[0] for o in definition.options.values()]

    @property
    def native_value(self) -> Any:
        d = self.definition
        value = self.coordinator.value(d.address, d.dtype)
        if value is None:
            return None
        if d.options is not None:
            option = d.options.get(int(value))
            return option[0] if option else None
        return value


class DeltaTSensor(HeatPumpEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE_DELTA if hasattr(
        SensorDeviceClass, "TEMPERATURE_DELTA") else None
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: HeatPumpCoordinator, definition: Base) -> None:
        super().__init__(coordinator, "sensor", definition)

    @property
    def native_value(self) -> float | None:
        t_in = self.coordinator.value(REG_INLET, "temp")
        t_out = self.coordinator.value(REG_OUTLET, "temp")
        if t_in is None or t_out is None:
            return None
        return round(t_out - t_in, 1)


class ThermalPowerSensor(HeatPumpEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: HeatPumpCoordinator, definition: Base) -> None:
        super().__init__(coordinator, "sensor", definition)

    @property
    def native_value(self) -> float | None:
        flow = self.coordinator.value(REG_FLOW, "d9")
        t_in = self.coordinator.value(REG_INLET, "temp")
        t_out = self.coordinator.value(REG_OUTLET, "temp")
        if flow is None or t_in is None or t_out is None:
            return None
        if flow <= 0:
            return 0.0
        return round(flow * (t_out - t_in) * WATER_HEAT_CAPACITY, 2)


def active_faults(raw: dict[int, int]) -> list[tuple[str, str, str]]:
    """Return (key, en, uk) for every active fault bit, including undocumented bits."""
    known = {(reg, bit): (key, en, uk) for reg, bit, key, en, uk in FAULT_BITS}
    result: list[tuple[str, str, str]] = []
    for reg in FAULT_REGISTERS:
        value = raw.get(reg) or 0
        for bit in range(16):
            if value & (1 << bit):
                result.append(known.get((reg, bit)) or (
                    f"fault_{reg}_bit{bit}", f"Fault {reg} bit {bit}", f"Аварія {reg} біт {bit}"))
    return result


class ActiveFaultsSensor(HeatPumpEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: HeatPumpCoordinator, definition: Base) -> None:
        super().__init__(coordinator, "sensor", definition)

    @property
    def native_value(self) -> int:
        return len(active_faults(self.coordinator.data or {}))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        faults = active_faults(self.coordinator.data or {})
        raw = self.coordinator.data or {}
        return {
            "faults": [f[0] for f in faults],
            "faults_en": [f[1] for f in faults],
            "faults_uk": [f[2] for f in faults],
            "registers": {str(r): f"0x{raw.get(r, 0):04X}" for r in FAULT_REGISTERS},
        }


class FirmwareSensor(HeatPumpEntity, SensorEntity):
    def __init__(self, coordinator: HeatPumpCoordinator, definition: Base) -> None:
        super().__init__(coordinator, "sensor", definition)

    @property
    def native_value(self) -> str | None:
        return self.coordinator.firmware


class ControllerTimeSensor(HeatPumpEntity, SensorEntity):
    """Controller RTC; None while the clock is unset (then disinfection cannot run)."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: HeatPumpCoordinator, definition: Base) -> None:
        super().__init__(coordinator, "sensor", definition)

    @property
    def native_value(self) -> Any:
        return controller_time(self.coordinator.data or {}, dt_util.DEFAULT_TIME_ZONE)
