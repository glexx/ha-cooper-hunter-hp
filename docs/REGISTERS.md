# Register map (holding registers, FC03 read / FC06 write)

Generated from `custom_components/cooper_hunter_hp/registers.py`. Controller pages: 1001–1090, 1091–1180, 1181–1270 (parameters), 2001–2090, 2091–2180 (status); the first 10 registers of every page are a header (firmware id, page start address).

System clock: 1250 enable, 1251 minute, 1252 hour, 1253 day, 1254 month, 1255 year (2000+N). The controller schedules legionella disinfection itself (registers 1152–1156) and never runs it while the clock is unset, so the integration keeps these registers in sync with Home Assistant time automatically.

## Writable

| Address | Entity | Type / scale | Range / options | Name |
|---|---|---|---|---|
| 1011 | `switch.power` | u16 | 0/1 | Power |
| 1012 | `select.operating_mode` | enum | 0=Hot water, 1=Heating, 2=Cooling, 3=Hot water + heating, 4=Hot water + cooling | Operating mode |
| 1016 | `button.manual_defrost` | bit 0 |  | Start manual defrost |
| 1018 | `switch.power_off_memory` | u16 | 0/1 | Power-off memory |
| 1021 | `switch.cooling_enabled` | u16 | 0/1 | Cooling function enabled |
| 1030 | `switch.silent_mode` | u16 | 0/1 | Silent mode |
| 1031 | `number.heater_off_delta` | ×0.1 (signed) | 0…30 °C | Electric heater off difference |
| 1032 | `select.electric_heater_stage` | enum | 1=Stage 1, 2=Stage 2, 3=Stage 3 | Electric heater stages |
| 1035 | `select.temperature_control_source` | enum | 0=Outlet water temperature, 1=Room temperature, 2=Buffer tank temperature, 3=Inlet water temperature | Temperature control source |
| 1037 | `number.shutdown_ambient` | ×0.1 (signed) | -40…10 °C | Shutdown outdoor temperature |
| 1045 | `number.forced_dhw_time` | ×1 | 1…300 min | Mode switch time (DHW/heating) |
| 1049 | `number.heater_on_ambient` | ×0.1 (signed) | -30…60 °C | Electric heater enable outdoor temp |
| 1050 | `number.heater_delay` | ×1 | 10…999 min | Electric heater delay after compressor |
| 1051 | `number.min_cooling_ambient` | ×0.1 (signed) | -30…60 °C | Min outdoor temp for cooling |
| 1063 | `number.heater_on_delta` | ×0.1 (signed) | 0…20 °C | Electric heater on difference |
| 1126 | `switch.heater_during_defrost` | u16 | 0/1 | Electric heater during defrost |
| 1129 | `select.defrost_heat_source` | enum | 0=Stay on current circuit, 1=DHW circuit, 2=Heating circuit | Defrost heat source |
| 1152 | `number.disinfection_temperature` | ×0.1 (signed) | 60…70 °C | Disinfection temperature |
| 1153 | `number.disinfection_duration` | ×1 | 0…60 min | Disinfection duration |
| 1154 | `number.disinfection_start_hour` | ×1 | 0…23 h | Disinfection start hour |
| 1155 | `number.disinfection_interval` | ×1 | 1…30 d | Disinfection interval |
| 1156 | `switch.disinfection` | u16 | 0/1 | Legionella disinfection |
| 1157 | `number.dhw_setpoint` | ×0.1 (signed) | 10…75 °C | DHW setpoint |
| 1158 | `number.heating_setpoint` | ×0.1 (signed) | 15…75 °C | Heating setpoint |
| 1159 | `number.cooling_setpoint` | ×0.1 (signed) | 5…28 °C | Cooling setpoint |
| 1160 | `number.heating_restart_delta` | ×0.1 (signed) | 0…10 °C | Heating restart difference |
| 1161 | `number.heating_standby_delta` | ×0.1 (signed) | 0…10 °C | Heating standby difference |
| 1162 | `number.cooling_setpoint_min` | ×0.1 (signed) | -30…80 °C | Cooling setpoint minimum |
| 1163 | `number.cooling_setpoint_max` | ×0.1 (signed) | -30…80 °C | Cooling setpoint maximum |
| 1164 | `number.heating_setpoint_min` | ×0.1 (signed) | -30…99 °C | Heating setpoint minimum |
| 1165 | `number.heating_setpoint_max` | ×0.1 (signed) | -30…99 °C | Heating setpoint maximum |
| 1173 | `select.electric_heater_mode` | enum | 0=Not available, 1=Main water circuit, 2=DHW tank, 3=Buffer tank | Electric heater location |
| 1174 | `number.cooling_restart_delta` | ×0.1 (signed) | 0…10 °C | Cooling restart difference |
| 1175 | `number.cooling_standby_delta` | ×0.1 (signed) | 0…10 °C | Cooling standby difference |
| 1176 | `number.dhw_setpoint_min` | ×0.1 (signed) | 0…85 °C | DHW setpoint minimum |
| 1177 | `number.dhw_setpoint_max` | ×0.1 (signed) | 0…85 °C | DHW setpoint maximum |
| 1192 | `number.auto_heating_ambient` | ×0.1 (signed) | 5…20 °C | Outdoor temp for auto heating |
| 1195 | `number.dhw_restart_delta` | ×0.1 (signed) | 0…10 °C | DHW restart difference |
| 1196 | `number.dhw_standby_delta` | ×0.1 (signed) | 0…10 °C | DHW standby difference |
| 1197 | `select.circulation_pump_mode` | enum | 0=Always on, 1=Saving, 2=Interval | Main pump mode |
| 1198 | `number.main_pump_interval` | ×1 | 1…120 min | Main pump interval |
| 1199 | `number.main_pump_runtime` | ×1 | 1…30 min | Main pump run duration |
| 1201 | `select.dhw_pump_mode` | enum | 0=Always on, 1=Saving, 2=Interval | DHW pump mode |
| 1202 | `switch.manual_water_pump` | u16 | 0/1 | Main pump manual control |
| 1205 | `number.circulation_pump_speed` | ×1 | 0…100 % | Circulation pump speed |
| 1228 | `number.max_outlet_heating` | ×0.1 (signed) | 20…85 °C | Max outlet temperature in heating |
| 1231 | `number.heater_no_delay_ambient` | ×0.1 (signed) | -50…20 °C | Outdoor temp for heater without delay |
| 1234 | `number.curve_slope` | ×0.1 | 0…3.5 | Weather curve slope |
| 1235 | `number.curve_offset` | ×0.1 (signed) | 0…75 °C | Weather curve offset |
| 1236 | `switch.weather_compensation` | u16 | 0/1 | Weather compensation |
| 1238 | `number.maximum_outlet_temperature` | ×0.1 (signed) | 40…95 °C | Max heat pump outlet temperature |
| 1239 | `number.room_setpoint` | ×0.1 (signed) | 5…27 °C | Room setpoint |

## Read-only

| Address | Entity | Type / scale | Unit / options | Name |
|---|---|---|---|---|
| 2012 | `sensor.operating_state` | enum | 0=Cooling, 1=Heating, 2=Defrost, 3=Disinfection, 4=Hot water | Operating state |
| 2013 | `sensor.current_temperature_target` | ×0.1 (signed) | °C | Active target temperature |
| 2014 | `sensor.compensated_temperature_target` | ×0.1 (signed) | °C | Standby target temperature |
| 2019 | `sensor.output_status_register` | ×1 |  | Output status register |
| 2020 | `sensor.eev_steps` | ×1 | steps | EEV opening |
| 2022 | `sensor.evi_eev_steps` | ×1 | steps | EVI EEV opening |
| 2023 | `sensor.compressor_starts` | ×1 |  | Compressor starts |
| 2024 | `sensor.backup_heater_dhw_runtime` | ×1 | h | Backup heater runtime (DHW) |
| 2025 | `sensor.backup_heater_heating_runtime` | ×1 | h | Backup heater runtime (heating) |
| 2029 | `sensor.input_current_1` | ×0.1 | A | Input current L1 |
| 2030 | `sensor.input_current_2` | ×0.1 | A | Input current L2 |
| 2031 | `sensor.input_current_3` | ×0.1 | A | Input current L3 |
| 2032 | `sensor.compressor_runtime` | ×1 | h | Compressor running time |
| 2034 | `sensor.input_status_register` | ×1 |  | Input status register |
| 2035 | `sensor.heating_return_temperature` | ×0.1 (signed) | °C | Heating return water temperature (T40) |
| 2036 | `sensor.heating_leaving_temperature` | ×0.1 (signed) | °C | Heating leaving water temperature (T41) |
| 2037 | `sensor.mix_tube_temperature` | ×0.1 (signed) | °C | Mixing tube outlet temperature (T42) |
| 2038 | `sensor.dhw_return_temperature` | ×0.1 (signed) | °C | DHW return water temperature (T43) |
| 2039 | `sensor.dhw_leaving_temperature` | ×0.1 (signed) | °C | DHW leaving water temperature (T44) |
| 2042 | `sensor.compressor_phase_current` | ×0.1 | A | Compressor phase current |
| 2043 | `sensor.dc_bus_voltage` | ×1 | V | DC bus voltage |
| 2044 | `sensor.ipm_temperature` | ×0.1 (signed) | °C | IPM temperature |
| 2045 | `sensor.water_inlet_temperature` | ×0.1 (signed) | °C | Water inlet temperature |
| 2046 | `sensor.water_outlet_temperature` | ×0.1 (signed) | °C | Water outlet temperature |
| 2047 | `sensor.dhw_tank_temperature` | ×0.1 (signed) | °C | DHW tank temperature |
| 2048 | `sensor.outdoor_temperature` | ×0.1 (signed) | °C | Outdoor temperature |
| 2049 | `sensor.coil_temperature` | ×0.1 (signed) | °C | Coil temperature |
| 2050 | `sensor.distributor_tube_temperature` | ×0.1 (signed) | °C | Distributor tube temperature |
| 2051 | `sensor.suction_temperature` | ×0.1 (signed) | °C | Suction temperature |
| 2052 | `sensor.buffer_tank_temperature` | ×0.1 (signed) | °C | Buffer tank temperature |
| 2053 | `sensor.discharge_temperature` | ×0.1 (signed) | °C | Discharge temperature |
| 2054 | `sensor.power_input` | ×0.1 | kW | Power input |
| 2055 | `sensor.antifreeze_temperature` | ×0.1 (signed) | °C | Antifreeze temperature |
| 2057 | `sensor.ac_input_current` | ×0.1 | A | AC input current |
| 2058 | `sensor.room_temperature` | ×0.1 (signed) | °C | Room temperature |
| 2059 | `sensor.heating_capacity` | ×0.1 | kW | Heat output |
| 2060 | `sensor.cop` | ×0.01 |  | COP |
| 2062 | `sensor.ac_input_voltage` | ×1 | V | AC input voltage |
| 2063 | `sensor.evi_inlet_temperature` | ×0.1 (signed) | °C | EVI inlet temperature |
| 2064 | `sensor.evi_outlet_temperature` | ×0.1 (signed) | °C | EVI outlet temperature |
| 2065 | `sensor.evaporation_temperature` | ×0.1 (signed) | °C | Evaporation temperature |
| 2066 | `sensor.exhaust_superheat` | ×0.1 (signed) | °C | Discharge superheat |
| 2067 | `sensor.superheat` | ×0.1 (signed) | °C | Suction superheat |
| 2068 | `sensor.outlet_after_heater_temperature` | ×0.1 (signed) | °C | Outlet after electric heater |
| 2069 | `sensor.low_pressure` | ×0.1 | bar | Low pressure |
| 2071 | `sensor.compressor_target_frequency` | ×1 | Hz | Compressor target frequency |
| 2072 | `sensor.compressor_frequency` | ×1 | Hz | Compressor frequency |
| 2073 | `sensor.compressor_max_frequency` | ×1 | Hz | Compressor max frequency (driver) |
| 2074 | `sensor.fan_1_speed` | ×1 | rpm | Fan 1 speed |
| 2075 | `sensor.fan_2_speed` | ×1 | rpm | Fan 2 speed |
| 2076 | `sensor.fan_target_speed` | ×1 | rpm | Fan target speed |
| 2077 | `sensor.water_flow` | ×0.01 | m³/h | Water flow |
| 2078 | `sensor.energy_consumption` | 32-bit (H,L) | kWh | Energy consumption (total) |
| 2080 | `sensor.driver_board_status` | ×1 |  | Driver board status |
| 2081 | `sensor.fault_register_2081` | ×1 |  | Fault register 2081 |
| 2082 | `sensor.fault_register_2082` | ×1 |  | Fault register 2082 |
| 2083 | `sensor.fault_register_2083` | ×1 |  | Fault register 2083 |
| 2084 | `sensor.fault_register_2084` | ×1 |  | Fault register 2084 |
| 2085 | `sensor.fault_register_2085` | ×1 |  | Fault register 2085 |
| 2086 | `sensor.fault_register_2086` | ×1 |  | Fault register 2086 |
| 2087 | `sensor.fault_register_2087` | ×1 |  | Fault register 2087 |
| 2088 | `sensor.fault_register_2088` | ×1 |  | Fault register 2088 |
| 2089 | `sensor.fault_register_2089` | ×1 |  | Fault register 2089 |
| 2090 | `sensor.fault_register_2090` | ×1 |  | Fault register 2090 |
| 2115 | `sensor.main_pump_pwm_output` | ×1 | % | Main pump PWM output |
| 2116 | `sensor.main_pump_pwm_feedback` | ×1 | % | Main pump PWM feedback |
| 2117 | `sensor.heating_energy_consumed` | 32-bit (H,L) | kWh | Heating energy consumed |
| 2119 | `sensor.heating_energy_generated` | 32-bit (H,L) | kWh | Heating energy generated |
| 2121 | `sensor.cooling_energy_consumed` | 32-bit (H,L) | kWh | Cooling energy consumed |
| 2123 | `sensor.cooling_energy_generated` | 32-bit (H,L) | kWh | Cooling energy generated |
| 2125 | `sensor.dhw_energy_consumed` | 32-bit (H,L) | kWh | DHW energy consumed |
| 2127 | `sensor.dhw_energy_generated` | 32-bit (H,L) | kWh | DHW energy generated |
| 2144 | `sensor.display_comm_success` | ×1 | % | Display communication quality |
| 2145 | `sensor.inverter_comm_success` | ×1 | % | Inverter communication quality |

## Bits

| Register | Bit | Entity | Name |
|---|---|---|---|
| 2011 | 0 | `binary_sensor.power_state` | Unit running |
| 2012 | ==2 | `binary_sensor.defrost_active` | Defrost |
| 2012 | ==3 | `binary_sensor.disinfection_active` | Disinfection running |
| 2019 | 10 | `binary_sensor.alarm_output` | Alarm output |
| 2019 | 11 | `binary_sensor.crankcase_heater` | Crankcase heater |
| 2019 | 12 | `binary_sensor.chassis_heater` | Chassis heater |
| 2019 | 13 | `binary_sensor.heat_pump_enabled` | Heat pump output |
| 2019 | 14 | `binary_sensor.hydrobox_electric_heater` | Hydrobox electric heater |
| 2019 | 15 | `binary_sensor.tank_electric_heater` | Tank electric heater |
| 2019 | 2 | `binary_sensor.fan_high_speed` | Fan high speed |
| 2019 | 3 | `binary_sensor.fan_low_speed` | Fan low speed |
| 2019 | 4 | `binary_sensor.main_circulation_pump` | Main circulation pump |
| 2019 | 5 | `binary_sensor.dhw_pump_running` | DHW pump |
| 2019 | 6 | `binary_sensor.four_way_valve` | Four-way valve |
| 2019 | 7 | `binary_sensor.electric_heater_stage_1` | Electric heater stage 1 |
| 2019 | 8 | `binary_sensor.electric_heater_stage_2` | Electric heater stage 2 |
| 2019 | 9 | `binary_sensor.dhw_3_way_valve` | DHW 3-way valve |
| 2034 | 0 | `binary_sensor.high_pressure_switch` | High pressure switch |
| 2034 | 1 | `binary_sensor.low_pressure_switch` | Low pressure switch |
| 2034 | 2 | `binary_sensor.water_flow_detected` | Water flow (inverted) |
| 2034 | 3 | `binary_sensor.electric_heater_overload_input` | Electric heater overload input |
| 2034 | 4 | `binary_sensor.emergency_input` | Emergency input |
| 2034 | 5 | `binary_sensor.ac_mode_input` | Heating/cooling demand input |
| 2034 | 6 | `binary_sensor.dhw_mode_input` | DHW demand input |
| 2034 | 9 | `binary_sensor.ac_switch` | AC linkage switch |
| 2081 | 0 | `binary_sensor.ipm_overcurrent_fault` | IPM overcurrent |
| 2081 | 1 | `binary_sensor.compressor_drive_fault` | Compressor drive fault |
| 2081 | 10 | `binary_sensor.ac_overcurrent` | AC overcurrent |
| 2081 | 2 | `binary_sensor.compressor_overcurrent` | Compressor overcurrent |
| 2081 | 3 | `binary_sensor.ac_phase_loss` | Input phase loss |
| 2081 | 4 | `binary_sensor.ipm_sampling_fault` | IPM current sampling fault |
| 2081 | 5 | `binary_sensor.drive_board_overheat` | Drive board overheat |
| 2081 | 6 | `binary_sensor.refrigerant_charge_fault` | Refrigerant charge fault |
| 2081 | 7 | `binary_sensor.dc_bus_overvoltage` | DC bus overvoltage |
| 2081 | 8 | `binary_sensor.dc_bus_undervoltage` | DC bus undervoltage |
| 2081 | 9 | `binary_sensor.ac_undervoltage` | AC undervoltage |
| 2082 | 0 | `binary_sensor.ipm_overheat_protection` | IPM overheat protection |
| 2082 | 1 | `binary_sensor.compressor_phase_loss` | Compressor phase loss |
| 2082 | 15 | `binary_sensor.compressor_overspeed_protection` | Compressor overspeed |
| 2082 | 6 | `binary_sensor.eeprom_fault` | EEPROM fault |
| 2082 | 7 | `binary_sensor.ac_overvoltage_protection` | AC overvoltage protection |
| 2083 | 0 | `binary_sensor.compressor_frequency_reduction_warning` | Compressor frequency limited |
| 2083 | 1 | `binary_sensor.weak_magnetic_field_warning` | Field weakening warning |
| 2083 | 2 | `binary_sensor.power_module_overheat_warning` | Power module overheat warning |
| 2083 | 5 | `binary_sensor.eeprom_warning` | EEPROM warning |
| 2083 | 7 | `binary_sensor.compressor_start_failure` | Compressor start failure |
| 2085 | 10 | `binary_sensor.freeze_protection_stage_1` | Freeze protection stage 1 |
| 2085 | 11 | `binary_sensor.freeze_protection_stage_2` | Freeze protection stage 2 |
| 2085 | 12 | `binary_sensor.system_freeze_protection` | System freeze protection |
| 2085 | 14 | `binary_sensor.room_temperature_sensor_fault` | Room temperature sensor fault |
| 2085 | 2 | `binary_sensor.heating_return_sensor_fault` | Heating return sensor fault |
| 2085 | 3 | `binary_sensor.heating_outlet_sensor_fault` | Heating outlet sensor fault |
| 2085 | 4 | `binary_sensor.high_pressure_protection` | High pressure protection |
| 2085 | 6 | `binary_sensor.low_pressure_protection` | Low pressure protection |
| 2085 | 8 | `binary_sensor.water_flow_protection` | Water flow protection |
| 2085 | 9 | `binary_sensor.electric_heater_overload_protection` | Electric heater overload |
| 2086 | 0 | `binary_sensor.discharge_overtemperature_protection` | Discharge overtemperature |
| 2086 | 3 | `binary_sensor.fan_1_overload_limitation` | Fan 1 overload |
| 2086 | 4 | `binary_sensor.fan_2_overload_limitation` | Fan 2 overload |
| 2086 | 5 | `binary_sensor.excessive_water_delta_t_protection` | Excessive water ΔT |
| 2086 | 6 | `binary_sensor.outlet_water_overtemperature_protection` | Outlet water overtemperature |
| 2086 | 7 | `binary_sensor.evaporator_outlet_sensor_fault` | Evaporator outlet sensor fault |
| 2086 | 8 | `binary_sensor.return_water_sensor_fault` | Return water sensor fault |
| 2086 | 9 | `binary_sensor.outlet_water_sensor_fault` | Outlet water sensor fault |
| 2087 | 12 | `binary_sensor.repeated_freeze_protection` | Repeated freeze protection |
| 2087 | 4 | `binary_sensor.repeated_high_pressure_protection` | Repeated high pressure protection |
| 2087 | 6 | `binary_sensor.repeated_low_pressure_protection` | Repeated low pressure protection |
| 2087 | 8 | `binary_sensor.repeated_water_flow_protection` | Repeated water flow protection |
| 2087 | 9 | `binary_sensor.repeated_electric_heater_protection` | Repeated electric heater protection |
| 2088 | 0 | `binary_sensor.repeated_discharge_overtemperature` | Repeated discharge overtemperature |
| 2088 | 2 | `binary_sensor.repeated_excessive_delta_t` | Repeated excessive ΔT |
| 2088 | 3 | `binary_sensor.repeated_low_outlet_temperature` | Repeated low outlet temperature |
| 2088 | 4 | `binary_sensor.repeated_high_outlet_temperature` | Repeated high outlet temperature |
| 2089 | 0 | `binary_sensor.water_inlet_sensor_fault` | Water inlet sensor fault |
| 2089 | 1 | `binary_sensor.water_outlet_sensor_fault` | Water outlet sensor fault |
| 2089 | 10 | `binary_sensor.evi_outlet_sensor_fault` | EVI outlet sensor fault |
| 2089 | 11 | `binary_sensor.discharge_temperature_sensor_fault` | Discharge sensor fault |
| 2089 | 2 | `binary_sensor.heat_exchanger_sensor_fault` | Coil sensor fault |
| 2089 | 3 | `binary_sensor.outdoor_temperature_sensor_fault` | Outdoor temperature sensor fault |
| 2089 | 4 | `binary_sensor.return_air_sensor_fault` | Suction sensor fault |
| 2089 | 5 | `binary_sensor.anti_freeze_sensor_fault` | Antifreeze sensor fault |
| 2089 | 6 | `binary_sensor.heat_exchanger_outlet_sensor_fault` | Heat exchanger outlet sensor fault |
| 2089 | 9 | `binary_sensor.evi_inlet_sensor_fault` | EVI inlet sensor fault |
| 2108 | 0 | `binary_sensor.silent_mode_active` | Silent mode active |
