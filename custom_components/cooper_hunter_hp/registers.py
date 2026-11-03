"""Declarative register map (LinkedGo/WarmLink controller used by CH-HP15UIMPZM).

Pure python on purpose: imported both by the integration and by
``scripts/gen_translations.py`` / ``scripts/gen_docs.py``.

Data types:
  temp  signed 16 bit, 0.1 °C, 32767 = sensor fault
  u16   unsigned, unit 1
  s16   signed, unit 1
  d5    unsigned, 0.1
  d9    unsigned, 0.01
  u32   two registers (high word first)
"""

from __future__ import annotations

from dataclasses import dataclass, field

DIAG = "diagnostic"
CONFIG = "config"


@dataclass(frozen=True, kw_only=True)
class Base:
    key: str
    en: str
    uk: str
    category: str | None = None
    enabled: bool = True
    icon: str | None = None


@dataclass(frozen=True, kw_only=True)
class SensorDef(Base):
    address: int
    dtype: str = "u16"
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = "measurement"
    precision: int | None = None
    options: dict[int, tuple[str, str, str]] | None = None  # enum: value -> (key, en, uk)


@dataclass(frozen=True, kw_only=True)
class BinaryDef(Base):
    address: int
    bit: int | None = None  # None -> compare with `equals`
    equals: int | None = None
    invert: bool = False
    device_class: str | None = None


@dataclass(frozen=True, kw_only=True)
class NumberDef(Base):
    address: int
    dtype: str = "temp"
    min: float
    max: float
    step: float = 1
    unit: str | None = None
    device_class: str | None = None
    min_reg: int | None = None  # dynamic limits taken from other registers
    max_reg: int | None = None
    mode: str = "box"


@dataclass(frozen=True, kw_only=True)
class SelectDef(Base):
    address: int
    options: dict[int, tuple[str, str, str]] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class SwitchDef(Base):
    address: int
    on: int = 1
    off: int = 0


@dataclass(frozen=True, kw_only=True)
class ButtonDef(Base):
    address: int
    bit: int


C = "°C"

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------
MODE_OPTIONS: dict[int, tuple[str, str, str]] = {
    0: ("dhw", "Hot water", "Гаряча вода"),
    1: ("heating", "Heating", "Опалення"),
    2: ("cooling", "Cooling", "Охолодження"),
    3: ("dhw_heating", "Hot water + heating", "Гаряча вода + опалення"),
    4: ("dhw_cooling", "Hot water + cooling", "Гаряча вода + охолодження"),
}
MODE_STATE_OPTIONS: dict[int, tuple[str, str, str]] = {
    0: ("cooling", "Cooling", "Охолодження"),
    1: ("heating", "Heating", "Опалення"),
    2: ("defrost", "Defrost", "Розморожування"),
    3: ("disinfection", "Disinfection", "Дезінфекція"),
    4: ("dhw", "Hot water", "Гаряча вода"),
}
PUMP_MODE_OPTIONS: dict[int, tuple[str, str, str]] = {
    0: ("always_on", "Always on", "Завжди увімкнено"),
    1: ("saving", "Saving", "Економний"),
    2: ("interval", "Interval", "Інтервальний"),
}
HEATER_LOCATION_OPTIONS: dict[int, tuple[str, str, str]] = {
    0: ("not_available", "Not available", "Відсутній"),
    1: ("main_circuit", "Main water circuit", "Основний водяний контур"),
    2: ("dhw_tank", "DHW tank", "Бак ГВП"),
    3: ("buffer_tank", "Buffer tank", "Буферний бак"),
}
TEMP_CONTROL_OPTIONS: dict[int, tuple[str, str, str]] = {
    0: ("outlet", "Outlet water temperature", "Температура подачі"),
    1: ("room", "Room temperature", "Кімнатна температура"),
    2: ("buffer", "Buffer tank temperature", "Температура буферного бака"),
    3: ("inlet", "Inlet water temperature", "Температура звороту"),
}
HEATER_STAGE_OPTIONS: dict[int, tuple[str, str, str]] = {
    1: ("stage_1", "Stage 1", "Ступінь 1"),
    2: ("stage_2", "Stage 2", "Ступінь 2"),
    3: ("stage_3", "Stage 3", "Ступінь 3"),
}
DEFROST_SOURCE_OPTIONS: dict[int, tuple[str, str, str]] = {
    0: ("current", "Stay on current circuit", "Поточний контур"),
    1: ("dhw", "DHW circuit", "Контур ГВП"),
    2: ("heating", "Heating circuit", "Контур опалення"),
}

# Registers that hold the "temperature control source" and are needed by climate.
REG_POWER = 1011
REG_MODE = 1012
REG_MANUAL_CONTROL = 1016
REG_TEMP_CONTROL = 1035
REG_DHW_SET = 1157
REG_HEAT_SET = 1158
REG_COOL_SET = 1159
REG_COOL_MIN, REG_COOL_MAX = 1162, 1163
REG_HEAT_MIN, REG_HEAT_MAX = 1164, 1165
REG_DHW_MIN, REG_DHW_MAX = 1176, 1177
REG_ROOM_SET = 1239
# Controller real-time clock; scheduled disinfection relies on it.
REG_TIME_ENABLE = 1250
REG_TIME_MINUTE = 1251
REG_TIME_HOUR = 1252
REG_TIME_DAY = 1253
REG_TIME_MONTH = 1254
REG_TIME_YEAR = 1255  # two digits, 2000 + N
REG_DISINFECTION_STANDBY = 1429  # on an optional page, absent on older firmware
REG_MODE_STATE = 2012
REG_COMP_FREQ = 2072
REG_INLET = 2045
REG_OUTLET = 2046
REG_DHW_TANK = 2047
REG_BUFFER = 2052
REG_ROOM = 2058
REG_FLOW = 2077
REG_CODE_VERSION = 2104
REG_MAINBOARD_VERSION = 2105
REG_DISPLAY_VERSION = 2112
FAULT_REGISTERS = tuple(range(2081, 2091))

# ---------------------------------------------------------------------------
# Sensors
# ---------------------------------------------------------------------------
T = "temperature"
SENSORS: tuple[SensorDef, ...] = (
    # Water / tanks
    SensorDef(key="water_inlet_temperature", address=2045, dtype="temp", unit=C, device_class=T,
              en="Water inlet temperature", uk="Температура звороту (вхід)"),
    SensorDef(key="water_outlet_temperature", address=2046, dtype="temp", unit=C, device_class=T,
              en="Water outlet temperature", uk="Температура подачі (вихід)"),
    SensorDef(key="dhw_tank_temperature", address=2047, dtype="temp", unit=C, device_class=T,
              en="DHW tank temperature", uk="Температура бака ГВП"),
    SensorDef(key="buffer_tank_temperature", address=2052, dtype="temp", unit=C, device_class=T,
              en="Buffer tank temperature", uk="Температура буферного бака"),
    SensorDef(key="outdoor_temperature", address=2048, dtype="temp", unit=C, device_class=T,
              en="Outdoor temperature", uk="Температура на вулиці"),
    SensorDef(key="room_temperature", address=2058, dtype="temp", unit=C, device_class=T, enabled=False,
              en="Room temperature", uk="Кімнатна температура"),
    SensorDef(key="outlet_after_heater_temperature", address=2068, dtype="temp", unit=C, device_class=T,
              enabled=False, category=DIAG,
              en="Outlet after electric heater", uk="Подача після електротену"),
    SensorDef(key="heating_return_temperature", address=2035, dtype="temp", unit=C, device_class=T,
              enabled=False, category=DIAG, en="Heating return water temperature (T40)",
              uk="Зворот опалення (T40)"),
    SensorDef(key="heating_leaving_temperature", address=2036, dtype="temp", unit=C, device_class=T,
              enabled=False, category=DIAG, en="Heating leaving water temperature (T41)",
              uk="Подача опалення (T41)"),
    SensorDef(key="mix_tube_temperature", address=2037, dtype="temp", unit=C, device_class=T,
              enabled=False, category=DIAG, en="Mixing tube outlet temperature (T42)",
              uk="Вихід змішувача (T42)"),
    SensorDef(key="dhw_return_temperature", address=2038, dtype="temp", unit=C, device_class=T,
              enabled=False, category=DIAG, en="DHW return water temperature (T43)",
              uk="Зворот ГВП (T43)"),
    SensorDef(key="dhw_leaving_temperature", address=2039, dtype="temp", unit=C, device_class=T,
              enabled=False, category=DIAG, en="DHW leaving water temperature (T44)",
              uk="Подача ГВП (T44)"),
    # Targets
    SensorDef(key="current_temperature_target", address=2013, dtype="temp", unit=C, device_class=T,
              en="Active target temperature", uk="Активна цільова температура"),
    SensorDef(key="compensated_temperature_target", address=2014, dtype="temp", unit=C, device_class=T,
              category=DIAG, en="Standby target temperature", uk="Цільова температура очікування"),
    # Refrigerant circuit
    SensorDef(key="coil_temperature", address=2049, dtype="temp", unit=C, device_class=T, category=DIAG,
              en="Coil temperature", uk="Температура випарника"),
    SensorDef(key="distributor_tube_temperature", address=2050, dtype="temp", unit=C, device_class=T,
              category=DIAG, en="Distributor tube temperature", uk="Температура розподільника"),
    SensorDef(key="suction_temperature", address=2051, dtype="temp", unit=C, device_class=T, category=DIAG,
              en="Suction temperature", uk="Температура всмоктування"),
    SensorDef(key="discharge_temperature", address=2053, dtype="temp", unit=C, device_class=T,
              category=DIAG, en="Discharge temperature", uk="Температура нагнітання"),
    SensorDef(key="antifreeze_temperature", address=2055, dtype="temp", unit=C, device_class=T,
              category=DIAG, en="Antifreeze temperature", uk="Температура антифризу"),
    SensorDef(key="evi_inlet_temperature", address=2063, dtype="temp", unit=C, device_class=T,
              category=DIAG, enabled=False, en="EVI inlet temperature", uk="Температура входу EVI"),
    SensorDef(key="evi_outlet_temperature", address=2064, dtype="temp", unit=C, device_class=T,
              category=DIAG, enabled=False, en="EVI outlet temperature", uk="Температура виходу EVI"),
    SensorDef(key="evaporation_temperature", address=2065, dtype="temp", unit=C, device_class=T,
              category=DIAG, enabled=False, en="Evaporation temperature", uk="Температура випаровування"),
    SensorDef(key="exhaust_superheat", address=2066, dtype="temp", unit=C, device_class=T,
              category=DIAG, enabled=False, en="Discharge superheat", uk="Перегрів нагнітання"),
    SensorDef(key="superheat", address=2067, dtype="temp", unit=C, device_class=T, category=DIAG,
              enabled=False, en="Suction superheat", uk="Перегрів всмоктування"),
    SensorDef(key="low_pressure", address=2069, dtype="d5", unit="bar", device_class="pressure",
              category=DIAG, precision=1, en="Low pressure", uk="Низький тиск"),
    SensorDef(key="eev_steps", address=2020, unit="steps", category=DIAG, icon="mdi:valve",
              en="EEV opening", uk="Відкриття ЕРВ"),
    SensorDef(key="evi_eev_steps", address=2022, unit="steps", category=DIAG, enabled=False,
              icon="mdi:valve", en="EVI EEV opening", uk="Відкриття ЕРВ EVI"),
    # Compressor / fans
    SensorDef(key="compressor_frequency", address=2072, unit="Hz", device_class="frequency",
              icon="mdi:sine-wave", en="Compressor frequency", uk="Частота компресора"),
    SensorDef(key="compressor_target_frequency", address=2071, unit="Hz", device_class="frequency",
              category=DIAG, en="Compressor target frequency", uk="Задана частота компресора"),
    SensorDef(key="compressor_max_frequency", address=2073, unit="Hz", device_class="frequency",
              category=DIAG, enabled=False, en="Compressor max frequency (driver)",
              uk="Макс. частота компресора (драйвер)"),
    SensorDef(key="fan_1_speed", address=2074, unit="rpm", icon="mdi:fan", en="Fan 1 speed",
              uk="Оберти вентилятора 1"),
    SensorDef(key="fan_2_speed", address=2075, unit="rpm", icon="mdi:fan", en="Fan 2 speed",
              uk="Оберти вентилятора 2"),
    SensorDef(key="fan_target_speed", address=2076, unit="rpm", icon="mdi:fan", category=DIAG,
              enabled=False, en="Fan target speed", uk="Задані оберти вентилятора"),
    SensorDef(key="compressor_starts", address=2023, state_class="total_increasing", category=DIAG,
              icon="mdi:counter", en="Compressor starts", uk="Кількість пусків компресора"),
    SensorDef(key="compressor_runtime", address=2032, unit="h", device_class="duration",
              state_class="total_increasing", category=DIAG,
              en="Compressor running time", uk="Напрацювання компресора"),
    SensorDef(key="backup_heater_dhw_runtime", address=2024, unit="h", device_class="duration",
              state_class="total_increasing", category=DIAG,
              en="Backup heater runtime (DHW)", uk="Напрацювання тену (ГВП)"),
    SensorDef(key="backup_heater_heating_runtime", address=2025, unit="h", device_class="duration",
              state_class="total_increasing", category=DIAG,
              en="Backup heater runtime (heating)", uk="Напрацювання тену (опалення)"),
    # Water flow / performance
    SensorDef(key="water_flow", enabled=False, address=2077, dtype="d9", unit="m³/h", device_class="volume_flow_rate",
              precision=2, icon="mdi:water-pump", en="Water flow", uk="Витрата води"),
    SensorDef(key="power_input", enabled=False, address=2054, dtype="d5", unit="kW", device_class="power", precision=1,
              en="Power input", uk="Споживана потужність"),
    SensorDef(key="heating_capacity", enabled=False, address=2059, dtype="d5", unit="kW", device_class="power",
              precision=1, en="Heat output", uk="Теплова потужність"),
    SensorDef(key="cop", enabled=False, address=2060, dtype="d9", precision=2, icon="mdi:gauge",
              en="COP", uk="COP"),
    SensorDef(key="energy_consumption", address=2078, dtype="u32", unit="kWh", device_class="energy",
              state_class="total_increasing", precision=0, en="Energy consumption (total)",
              uk="Спожита енергія (всього)"),
    SensorDef(key="heating_energy_consumed", address=2117, dtype="u32", unit="kWh", device_class="energy",
              state_class="total_increasing", enabled=False,
              en="Heating energy consumed", uk="Спожито на опалення"),
    SensorDef(key="heating_energy_generated", address=2119, dtype="u32", unit="kWh", device_class="energy",
              state_class="total_increasing", enabled=False,
              en="Heating energy generated", uk="Вироблено тепла на опалення"),
    SensorDef(key="cooling_energy_consumed", address=2121, dtype="u32", unit="kWh", device_class="energy",
              state_class="total_increasing", enabled=False,
              en="Cooling energy consumed", uk="Спожито на охолодження"),
    SensorDef(key="cooling_energy_generated", address=2123, dtype="u32", unit="kWh", device_class="energy",
              state_class="total_increasing", enabled=False,
              en="Cooling energy generated", uk="Вироблено холоду"),
    SensorDef(key="dhw_energy_consumed", address=2125, dtype="u32", unit="kWh", device_class="energy",
              state_class="total_increasing", enabled=False,
              en="DHW energy consumed", uk="Спожито на ГВП"),
    SensorDef(key="dhw_energy_generated", address=2127, dtype="u32", unit="kWh", device_class="energy",
              state_class="total_increasing", enabled=False,
              en="DHW energy generated", uk="Вироблено тепла на ГВП"),
    # Electrical
    SensorDef(key="ac_input_voltage", address=2062, unit="V", device_class="voltage", category=DIAG,
              en="AC input voltage", uk="Напруга живлення"),
    SensorDef(key="ac_input_current", enabled=False, address=2057, dtype="d5", unit="A", device_class="current",
              precision=1, category=DIAG, en="AC input current", uk="Струм живлення"),
    SensorDef(key="input_current_1", address=2029, dtype="d5", unit="A", device_class="current",
              precision=1, category=DIAG, enabled=False, en="Input current L1", uk="Струм L1"),
    SensorDef(key="input_current_2", address=2030, dtype="d5", unit="A", device_class="current",
              precision=1, category=DIAG, enabled=False, en="Input current L2", uk="Струм L2"),
    SensorDef(key="input_current_3", address=2031, dtype="d5", unit="A", device_class="current",
              precision=1, category=DIAG, enabled=False, en="Input current L3", uk="Струм L3"),
    SensorDef(key="compressor_phase_current", address=2042, dtype="d5", unit="A", device_class="current",
              precision=1, category=DIAG, en="Compressor phase current", uk="Фазний струм компресора"),
    SensorDef(key="dc_bus_voltage", address=2043, unit="V", device_class="voltage", category=DIAG,
              en="DC bus voltage", uk="Напруга DC-шини"),
    SensorDef(key="ipm_temperature", address=2044, dtype="temp", unit=C, device_class=T, category=DIAG,
              en="IPM temperature", uk="Температура IPM-модуля"),
    SensorDef(key="main_pump_pwm_output", address=2115, unit="%", category=DIAG, enabled=False,
              icon="mdi:pump", en="Main pump PWM output", uk="ШІМ насоса (вихід)"),
    SensorDef(key="main_pump_pwm_feedback", address=2116, unit="%", category=DIAG, enabled=False,
              icon="mdi:pump", en="Main pump PWM feedback", uk="ШІМ насоса (зворотний зв'язок)"),
    # State
    SensorDef(key="operating_state", address=2012, dtype="enum", state_class=None, device_class="enum",
              options=MODE_STATE_OPTIONS, icon="mdi:heat-pump",
              en="Operating state", uk="Поточний стан роботи"),
    SensorDef(key="driver_board_status", address=2080, state_class=None, category=DIAG, enabled=False,
              en="Driver board status", uk="Статус плати драйвера"),
    SensorDef(key="display_comm_success", address=2144, unit="%", category=DIAG, enabled=False,
              en="Display communication quality", uk="Якість зв'язку з пультом"),
    SensorDef(key="inverter_comm_success", address=2145, unit="%", category=DIAG, enabled=False,
              en="Inverter communication quality", uk="Якість зв'язку з інвертором"),
) + tuple(
    SensorDef(key=f"fault_register_{addr}", address=addr, state_class=None, category=DIAG, enabled=False,
              icon="mdi:alert-circle-outline",
              en=f"Fault register {addr}", uk=f"Регістр аварій {addr}")
    for addr in FAULT_REGISTERS
) + (
    SensorDef(key="output_status_register", address=2019, state_class=None, category=DIAG, enabled=False,
              en="Output status register", uk="Регістр стану виходів"),
    SensorDef(key="input_status_register", address=2034, state_class=None, category=DIAG, enabled=False,
              en="Input status register", uk="Регістр стану входів"),
)

# ---------------------------------------------------------------------------
# Binary sensors (bit definitions of 2019/2034/208x are not in the public
# LinkedGo table; they follow the Cooper&Hunter user manual).
# ---------------------------------------------------------------------------
_OUTPUT_BITS = (
    (2, "fan_high_speed", "Fan high speed", "Вентилятор: висока швидкість", None),
    (3, "fan_low_speed", "Fan low speed", "Вентилятор: низька швидкість", None),
    (4, "main_circulation_pump", "Main circulation pump", "Основний циркуляційний насос", "running"),
    (5, "dhw_pump_running", "DHW pump", "Насос ГВП", "running"),
    (6, "four_way_valve", "Four-way valve", "4-ходовий клапан", None),
    (7, "electric_heater_stage_1", "Electric heater stage 1", "Електротен ступінь 1", "heat"),
    (8, "electric_heater_stage_2", "Electric heater stage 2", "Електротен ступінь 2", "heat"),
    (9, "dhw_3_way_valve", "DHW 3-way valve", "3-ходовий клапан ГВП", None),
    (10, "alarm_output", "Alarm output", "Вихід аварії", "problem"),
    (11, "crankcase_heater", "Crankcase heater", "Підігрів картера", "heat"),
    (12, "chassis_heater", "Chassis heater", "Підігрів піддону", "heat"),
    (13, "heat_pump_enabled", "Heat pump output", "Вихід теплового насоса", None),
    (14, "hydrobox_electric_heater", "Hydrobox electric heater", "Електротен гідромодуля", "heat"),
    (15, "tank_electric_heater", "Tank electric heater", "Електротен бака", "heat"),
)
_INPUT_BITS = (
    (0, "high_pressure_switch", "High pressure switch", "Реле високого тиску"),
    (1, "low_pressure_switch", "Low pressure switch", "Реле низького тиску"),
    (3, "electric_heater_overload_input", "Electric heater overload input", "Вхід перевантаження тену"),
    (4, "emergency_input", "Emergency input", "Аварійний вхід"),
    (5, "ac_mode_input", "Heating/cooling demand input", "Вхід запиту опалення/охолодження"),
    (6, "dhw_mode_input", "DHW demand input", "Вхід запиту ГВП"),
    (9, "ac_switch", "AC linkage switch", "Вхід зв'язку з кондиціонером"),
)
# (register, bit, key, en, uk)
FAULT_BITS: tuple[tuple[int, int, str, str, str], ...] = (
    (2081, 0, "ipm_overcurrent_fault", "IPM overcurrent", "Перевантаження IPM за струмом"),
    (2081, 1, "compressor_drive_fault", "Compressor drive fault", "Несправність драйвера компресора"),
    (2081, 2, "compressor_overcurrent", "Compressor overcurrent", "Перевантаження компресора за струмом"),
    (2081, 3, "ac_phase_loss", "Input phase loss", "Втрата фази живлення"),
    (2081, 4, "ipm_sampling_fault", "IPM current sampling fault", "Помилка вимірювання струму IPM"),
    (2081, 5, "drive_board_overheat", "Drive board overheat", "Перегрів плати драйвера"),
    (2081, 6, "refrigerant_charge_fault", "Refrigerant charge fault", "Нестача холодоагенту"),
    (2081, 7, "dc_bus_overvoltage", "DC bus overvoltage", "Перенапруга DC-шини"),
    (2081, 8, "dc_bus_undervoltage", "DC bus undervoltage", "Низька напруга DC-шини"),
    (2081, 9, "ac_undervoltage", "AC undervoltage", "Низька напруга живлення"),
    (2081, 10, "ac_overcurrent", "AC overcurrent", "Перевантаження живлення за струмом"),
    (2082, 0, "ipm_overheat_protection", "IPM overheat protection", "Захист від перегріву IPM"),
    (2082, 1, "compressor_phase_loss", "Compressor phase loss", "Втрата фази компресора"),
    (2082, 6, "eeprom_fault", "EEPROM fault", "Помилка EEPROM"),
    (2082, 7, "ac_overvoltage_protection", "AC overvoltage protection", "Захист від перенапруги"),
    (2082, 15, "compressor_overspeed_protection", "Compressor overspeed", "Перевищення обертів компресора"),
    (2083, 0, "compressor_frequency_reduction_warning", "Compressor frequency limited",
     "Обмеження частоти компресора"),
    (2083, 1, "weak_magnetic_field_warning", "Field weakening warning", "Попередження: послаблення поля"),
    (2083, 2, "power_module_overheat_warning", "Power module overheat warning",
     "Попередження: перегрів силового модуля"),
    (2083, 5, "eeprom_warning", "EEPROM warning", "Попередження EEPROM"),
    (2083, 7, "compressor_start_failure", "Compressor start failure", "Невдалий пуск компресора"),
    (2085, 2, "heating_return_sensor_fault", "Heating return sensor fault", "Несправність датчика звороту опалення"),
    (2085, 3, "heating_outlet_sensor_fault", "Heating outlet sensor fault", "Несправність датчика подачі опалення"),
    (2085, 4, "high_pressure_protection", "High pressure protection", "Захист за високим тиском"),
    (2085, 6, "low_pressure_protection", "Low pressure protection", "Захист за низьким тиском"),
    (2085, 8, "water_flow_protection", "Water flow protection", "Захист за протоком води"),
    (2085, 9, "electric_heater_overload_protection", "Electric heater overload",
     "Перевантаження електротену"),
    (2085, 10, "freeze_protection_stage_1", "Freeze protection stage 1", "Захист від замерзання, ступінь 1"),
    (2085, 11, "freeze_protection_stage_2", "Freeze protection stage 2", "Захист від замерзання, ступінь 2"),
    (2085, 12, "system_freeze_protection", "System freeze protection", "Захист системи від замерзання"),
    (2085, 14, "room_temperature_sensor_fault", "Room temperature sensor fault",
     "Несправність кімнатного датчика"),
    (2086, 0, "discharge_overtemperature_protection", "Discharge overtemperature",
     "Перегрів нагнітання"),
    (2086, 3, "fan_1_overload_limitation", "Fan 1 overload", "Перевантаження вентилятора 1"),
    (2086, 4, "fan_2_overload_limitation", "Fan 2 overload", "Перевантаження вентилятора 2"),
    (2086, 5, "excessive_water_delta_t_protection", "Excessive water ΔT", "Завелика різниця температур води"),
    (2086, 6, "outlet_water_overtemperature_protection", "Outlet water overtemperature",
     "Перегрів води на подачі"),
    (2086, 7, "evaporator_outlet_sensor_fault", "Evaporator outlet sensor fault",
     "Несправність датчика виходу випарника"),
    (2086, 8, "return_water_sensor_fault", "Return water sensor fault", "Несправність датчика звороту"),
    (2086, 9, "outlet_water_sensor_fault", "Outlet water sensor fault", "Несправність датчика подачі"),
    (2087, 4, "repeated_high_pressure_protection", "Repeated high pressure protection",
     "Повторний захист за високим тиском"),
    (2087, 6, "repeated_low_pressure_protection", "Repeated low pressure protection",
     "Повторний захист за низьким тиском"),
    (2087, 8, "repeated_water_flow_protection", "Repeated water flow protection",
     "Повторний захист за протоком"),
    (2087, 9, "repeated_electric_heater_protection", "Repeated electric heater protection",
     "Повторний захист електротену"),
    (2087, 12, "repeated_freeze_protection", "Repeated freeze protection", "Повторний захист від замерзання"),
    (2088, 0, "repeated_discharge_overtemperature", "Repeated discharge overtemperature",
     "Повторний перегрів нагнітання"),
    (2088, 2, "repeated_excessive_delta_t", "Repeated excessive ΔT", "Повторна завелика різниця температур"),
    (2088, 3, "repeated_low_outlet_temperature", "Repeated low outlet temperature",
     "Повторна низька температура подачі"),
    (2088, 4, "repeated_high_outlet_temperature", "Repeated high outlet temperature",
     "Повторна висока температура подачі"),
    (2089, 0, "water_inlet_sensor_fault", "Water inlet sensor fault", "Несправність датчика входу води"),
    (2089, 1, "water_outlet_sensor_fault", "Water outlet sensor fault", "Несправність датчика виходу води"),
    (2089, 2, "heat_exchanger_sensor_fault", "Coil sensor fault", "Несправність датчика випарника"),
    (2089, 3, "outdoor_temperature_sensor_fault", "Outdoor temperature sensor fault",
     "Несправність вуличного датчика"),
    (2089, 4, "return_air_sensor_fault", "Suction sensor fault", "Несправність датчика всмоктування"),
    (2089, 5, "anti_freeze_sensor_fault", "Antifreeze sensor fault", "Несправність датчика антифризу"),
    (2089, 6, "heat_exchanger_outlet_sensor_fault", "Heat exchanger outlet sensor fault",
     "Несправність датчика виходу теплообмінника"),
    (2089, 9, "evi_inlet_sensor_fault", "EVI inlet sensor fault", "Несправність датчика входу EVI"),
    (2089, 10, "evi_outlet_sensor_fault", "EVI outlet sensor fault", "Несправність датчика виходу EVI"),
    (2089, 11, "discharge_temperature_sensor_fault", "Discharge sensor fault",
     "Несправність датчика нагнітання"),
)

BINARY_SENSORS: tuple[BinaryDef, ...] = (
    BinaryDef(key="power_state", address=2011, bit=0, device_class="running",
              en="Unit running", uk="Насос увімкнено"),
    BinaryDef(key="defrost_active", address=2012, equals=2, icon="mdi:snowflake-melt",
              en="Defrost", uk="Розморожування"),
    BinaryDef(key="disinfection_active", address=2012, equals=3, icon="mdi:bacteria-outline",
              en="Disinfection running", uk="Дезінфекція триває"),
    BinaryDef(key="silent_mode_active", address=2108, bit=0, icon="mdi:volume-off", category=DIAG,
              en="Silent mode active", uk="Тихий режим активний"),
) + tuple(
    BinaryDef(key=k, address=2019, bit=b, device_class=dc, en=en, uk=uk,
              category=None if k in ("main_circulation_pump", "dhw_pump_running", "dhw_3_way_valve",
                                     "electric_heater_stage_1", "electric_heater_stage_2",
                                     "hydrobox_electric_heater", "tank_electric_heater") else DIAG)
    for b, k, en, uk, dc in _OUTPUT_BITS
) + tuple(
    BinaryDef(key=k, address=2034, bit=b, en=en, uk=uk, category=DIAG,
              device_class="problem" if k == "emergency_input" else None)
    for b, k, en, uk in _INPUT_BITS
) + (
    # Bit 2 is set while the flow switch is open (verified on a running unit).
    BinaryDef(key="water_flow_detected", address=2034, bit=2, invert=True, device_class="running",
              icon="mdi:waves-arrow-right", en="Water flow", uk="Протік води"),
) + tuple(
    BinaryDef(key=k, address=reg, bit=b, en=en, uk=uk, device_class="problem", category=DIAG)
    for reg, b, k, en, uk in FAULT_BITS
)

# ---------------------------------------------------------------------------
# Writable entities
# ---------------------------------------------------------------------------
SWITCHES: tuple[SwitchDef, ...] = (
    SwitchDef(key="power", address=1011, icon="mdi:power", en="Power", uk="Живлення"),
    SwitchDef(key="silent_mode", address=1030, icon="mdi:volume-off", en="Silent mode", uk="Тихий режим"),
    SwitchDef(key="weather_compensation", address=1236, icon="mdi:chart-bell-curve-cumulative",
              en="Weather compensation", uk="Погодозалежне регулювання"),
    SwitchDef(key="disinfection", address=1156, icon="mdi:bacteria-outline", category=CONFIG,
              en="Legionella disinfection", uk="Дезінфекція (легіонела)"),
    SwitchDef(key="disinfection_in_standby", address=REG_DISINFECTION_STANDBY,
              icon="mdi:bacteria-outline", category=CONFIG,
              en="Disinfection in standby & off mode", uk="Дезінфекція в режимі очікування/вимкнено"),
    SwitchDef(key="manual_water_pump", address=1202, icon="mdi:pump", category=CONFIG,
              en="Main pump manual control", uk="Ручне керування насосом"),
    SwitchDef(key="cooling_enabled", address=1021, icon="mdi:snowflake", category=CONFIG, enabled=False,
              en="Cooling function enabled", uk="Функцію охолодження дозволено"),
    SwitchDef(key="heater_during_defrost", address=1126, icon="mdi:heating-coil", category=CONFIG,
              enabled=False, en="Electric heater during defrost", uk="Електротен під час розморожування"),
    SwitchDef(key="power_off_memory", address=1018, icon="mdi:restore", category=CONFIG, enabled=False,
              en="Power-off memory", uk="Пам'ять стану після вимкнення живлення"),
)

SELECTS: tuple[SelectDef, ...] = (
    SelectDef(key="operating_mode", address=1012, options=MODE_OPTIONS, icon="mdi:heat-pump-outline",
              en="Operating mode", uk="Режим роботи"),
    SelectDef(key="electric_heater_mode", address=1173, options=HEATER_LOCATION_OPTIONS,
              icon="mdi:heating-coil", category=CONFIG,
              en="Electric heater location", uk="Розташування електротену"),
    SelectDef(key="circulation_pump_mode", address=1197, options=PUMP_MODE_OPTIONS, icon="mdi:pump",
              category=CONFIG, en="Main pump mode", uk="Режим основного насоса"),
    SelectDef(key="dhw_pump_mode", address=1201, options=PUMP_MODE_OPTIONS, icon="mdi:pump",
              category=CONFIG, en="DHW pump mode", uk="Режим насоса ГВП"),
    SelectDef(key="temperature_control_source", address=1035, options=TEMP_CONTROL_OPTIONS,
              icon="mdi:thermometer-check", category=CONFIG,
              en="Temperature control source", uk="Датчик регулювання"),
    SelectDef(key="electric_heater_stage", address=1032, options=HEATER_STAGE_OPTIONS,
              icon="mdi:heating-coil", category=CONFIG, enabled=False,
              en="Electric heater stages", uk="Кількість ступенів тену"),
    SelectDef(key="defrost_heat_source", address=1129, options=DEFROST_SOURCE_OPTIONS,
              icon="mdi:snowflake-melt", category=CONFIG, enabled=False,
              en="Defrost heat source", uk="Джерело тепла для розморожування"),
)

NUMBERS: tuple[NumberDef, ...] = (
    NumberDef(key="dhw_setpoint", address=REG_DHW_SET, min=10, max=75, step=0.5, unit=C, device_class=T,
              min_reg=REG_DHW_MIN, max_reg=REG_DHW_MAX, mode="slider",
              en="DHW setpoint", uk="Уставка ГВП"),
    NumberDef(key="heating_setpoint", address=REG_HEAT_SET, min=15, max=75, step=0.5, unit=C,
              device_class=T, min_reg=REG_HEAT_MIN, max_reg=REG_HEAT_MAX, mode="slider",
              en="Heating setpoint", uk="Уставка опалення"),
    NumberDef(key="cooling_setpoint", address=REG_COOL_SET, min=5, max=28, step=0.5, unit=C,
              device_class=T, min_reg=REG_COOL_MIN, max_reg=REG_COOL_MAX, mode="slider",
              en="Cooling setpoint", uk="Уставка охолодження"),
    NumberDef(key="room_setpoint", address=REG_ROOM_SET, min=5, max=27, step=0.5, unit=C, device_class=T,
              enabled=False, en="Room setpoint", uk="Уставка кімнатної температури"),
    NumberDef(key="curve_slope", address=1234, dtype="d5", min=0, max=3.5, step=0.1,
              icon="mdi:chart-line-variant", en="Weather curve slope", uk="Нахил погодної кривої"),
    NumberDef(key="curve_offset", address=1235, min=0, max=75, step=0.5, unit=C, device_class=T,
              icon="mdi:chart-line-variant", en="Weather curve offset", uk="Зсув погодної кривої"),
    NumberDef(key="forced_dhw_time", address=1045, dtype="u16", min=1, max=300, unit="min",
              device_class="duration", category=CONFIG, icon="mdi:timer-sync-outline",
              en="Mode switch time (DHW/heating)", uk="Час перемикання режимів ГВП/опалення"),
    NumberDef(key="maximum_outlet_temperature", address=1238, min=40, max=95, step=0.5, unit=C,
              device_class=T, category=CONFIG,
              en="Max heat pump outlet temperature", uk="Макс. температура подачі ТН"),
    NumberDef(key="max_outlet_heating", address=1228, min=20, max=85, step=0.5, unit=C, device_class=T,
              category=CONFIG, enabled=False,
              en="Max outlet temperature in heating", uk="Макс. температура подачі в опаленні"),
    NumberDef(key="main_pump_interval", address=1198, dtype="u16", min=1, max=120, unit="min",
              device_class="duration", category=CONFIG,
              en="Main pump interval", uk="Інтервал насоса"),
    NumberDef(key="main_pump_runtime", address=1199, dtype="u16", min=1, max=30, unit="min",
              device_class="duration", category=CONFIG,
              en="Main pump run duration", uk="Тривалість роботи насоса"),
    NumberDef(key="circulation_pump_speed", address=1205, dtype="u16", min=0, max=100, unit="%",
              category=CONFIG, enabled=False, icon="mdi:pump",
              en="Circulation pump speed", uk="Швидкість циркуляційного насоса"),
    NumberDef(key="disinfection_temperature", address=1152, min=60, max=70, step=1, unit=C,
              device_class=T, category=CONFIG,
              en="Disinfection temperature", uk="Температура дезінфекції"),
    NumberDef(key="disinfection_duration", address=1153, dtype="u16", min=0, max=60, unit="min",
              device_class="duration", category=CONFIG,
              en="Disinfection duration", uk="Тривалість дезінфекції"),
    NumberDef(key="disinfection_start_hour", address=1154, dtype="u16", min=0, max=23, unit="h",
              category=CONFIG, icon="mdi:clock-start",
              en="Disinfection start hour", uk="Година початку дезінфекції"),
    NumberDef(key="disinfection_interval", address=1155, dtype="u16", min=1, max=30, unit="d",
              device_class="duration", category=CONFIG,
              en="Disinfection interval", uk="Період дезінфекції"),
    NumberDef(key="heating_restart_delta", address=1160, min=0, max=10, step=0.5, unit=C,
              device_class="temperature_delta", category=CONFIG,
              en="Heating restart difference", uk="Гістерезис опалення (увімкнення)"),
    NumberDef(key="heating_standby_delta", address=1161, min=0, max=10, step=0.5, unit=C,
              device_class="temperature_delta", category=CONFIG,
              en="Heating standby difference", uk="Гістерезис опалення (очікування)"),
    NumberDef(key="cooling_restart_delta", address=1174, min=0, max=10, step=0.5, unit=C,
              device_class="temperature_delta", category=CONFIG, enabled=False,
              en="Cooling restart difference", uk="Гістерезис охолодження (увімкнення)"),
    NumberDef(key="cooling_standby_delta", address=1175, min=0, max=10, step=0.5, unit=C,
              device_class="temperature_delta", category=CONFIG, enabled=False,
              en="Cooling standby difference", uk="Гістерезис охолодження (очікування)"),
    NumberDef(key="dhw_restart_delta", address=1195, min=0, max=10, step=0.5, unit=C,
              device_class="temperature_delta", category=CONFIG,
              en="DHW restart difference", uk="Гістерезис ГВП (увімкнення)"),
    NumberDef(key="dhw_standby_delta", address=1196, min=0, max=10, step=0.5, unit=C,
              device_class="temperature_delta", category=CONFIG,
              en="DHW standby difference", uk="Гістерезис ГВП (очікування)"),
    NumberDef(key="heater_on_ambient", address=1049, min=-30, max=60, step=0.5, unit=C, device_class=T,
              category=CONFIG, en="Electric heater enable outdoor temp", uk="Вулична t° для дозволу тену"),
    NumberDef(key="heater_delay", address=1050, dtype="u16", min=10, max=999, unit="min",
              device_class="duration", category=CONFIG,
              en="Electric heater delay after compressor", uk="Затримка тену після компресора"),
    NumberDef(key="heater_on_delta", address=1063, min=0, max=20, step=0.5, unit=C,
              device_class="temperature_delta", category=CONFIG, enabled=False,
              en="Electric heater on difference", uk="Різниця увімкнення тену"),
    NumberDef(key="heater_off_delta", address=1031, min=0, max=30, step=0.5, unit=C,
              device_class="temperature_delta", category=CONFIG, enabled=False,
              en="Electric heater off difference", uk="Різниця вимкнення тену"),
    NumberDef(key="heater_no_delay_ambient", address=1231, min=-50, max=20, step=0.5, unit=C,
              device_class=T, category=CONFIG, enabled=False,
              en="Outdoor temp for heater without delay", uk="Вулична t° для тену без затримки"),
    NumberDef(key="shutdown_ambient", address=1037, min=-40, max=10, step=0.5, unit=C, device_class=T,
              category=CONFIG, enabled=False,
              en="Shutdown outdoor temperature", uk="Вулична t° зупинки ТН"),
    NumberDef(key="auto_heating_ambient", address=1192, min=5, max=20, step=0.5, unit=C, device_class=T,
              category=CONFIG, enabled=False,
              en="Outdoor temp for auto heating", uk="Вулична t° автозапуску опалення"),
    NumberDef(key="min_cooling_ambient", address=1051, min=-30, max=60, step=0.5, unit=C, device_class=T,
              category=CONFIG, enabled=False,
              en="Min outdoor temp for cooling", uk="Мін. вулична t° для охолодження"),
    NumberDef(key="dhw_setpoint_min", address=REG_DHW_MIN, min=0, max=85, step=0.5, unit=C,
              device_class=T, category=CONFIG, enabled=False,
              en="DHW setpoint minimum", uk="Мінімальна уставка ГВП"),
    NumberDef(key="dhw_setpoint_max", address=REG_DHW_MAX, min=0, max=85, step=0.5, unit=C,
              device_class=T, category=CONFIG, enabled=False,
              en="DHW setpoint maximum", uk="Максимальна уставка ГВП"),
    NumberDef(key="heating_setpoint_min", address=REG_HEAT_MIN, min=-30, max=99, step=0.5, unit=C,
              device_class=T, category=CONFIG, enabled=False,
              en="Heating setpoint minimum", uk="Мінімальна уставка опалення"),
    NumberDef(key="heating_setpoint_max", address=REG_HEAT_MAX, min=-30, max=99, step=0.5, unit=C,
              device_class=T, category=CONFIG, enabled=False,
              en="Heating setpoint maximum", uk="Максимальна уставка опалення"),
    NumberDef(key="cooling_setpoint_min", address=REG_COOL_MIN, min=-30, max=80, step=0.5, unit=C,
              device_class=T, category=CONFIG, enabled=False,
              en="Cooling setpoint minimum", uk="Мінімальна уставка охолодження"),
    NumberDef(key="cooling_setpoint_max", address=REG_COOL_MAX, min=-30, max=80, step=0.5, unit=C,
              device_class=T, category=CONFIG, enabled=False,
              en="Cooling setpoint maximum", uk="Максимальна уставка охолодження"),
)

BUTTONS: tuple[ButtonDef, ...] = (
    ButtonDef(key="manual_defrost", address=REG_MANUAL_CONTROL, bit=0, icon="mdi:snowflake-melt",
              category=CONFIG, en="Start manual defrost", uk="Запустити розморожування"),
)

# Derived (computed) sensors – translations only; logic lives in sensor.py.
DERIVED_SENSORS: tuple[Base, ...] = (
    Base(key="water_delta_t", en="Water ΔT (outlet − inlet)", uk="ΔT води (подача − зворот)",
         icon="mdi:thermometer-lines"),
    Base(key="thermal_power", en="Thermal power (calculated)", uk="Теплова потужність (розрахунок)",
         icon="mdi:fire", enabled=False),
    Base(key="active_faults", en="Active faults", uk="Активні аварії", icon="mdi:alert"),
    Base(key="firmware", en="Controller firmware", uk="Прошивка контролера", category=DIAG,
         icon="mdi:chip"),
    Base(key="controller_time", en="Controller time", uk="Час контролера", category=DIAG,
         icon="mdi:clock-outline"),
)
DERIVED_BINARY: tuple[Base, ...] = (
    Base(key="compressor_running", en="Compressor running", uk="Компресор працює"),
    Base(key="fault", en="Fault", uk="Аварія"),
)
CLIMATE_NAME = ("Heating / cooling", "Опалення / охолодження")
WATER_HEATER_NAME = ("Hot water", "Гаряча вода")
