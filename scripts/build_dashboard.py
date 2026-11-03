"""Build the Lovelace dashboard for the Cooper&Hunter heat pump integration.

Usage:
  python3 scripts/build_dashboard.py [--prefix hp] [--power-meter sensor.x_power]
        [--energy-meter sensor.x_energy] [--heat-meter sensor.y_heat] [--json out.json]

Writes dashboard/heat_pump_dashboard.yaml (needs PyYAML) and optionally JSON
(used to push the config through the Home Assistant websocket API).
Requires HACS frontend cards: Mushroom, ApexCharts.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "registers", ROOT / "custom_components" / "cooper_hunter_hp" / "registers.py")
R = importlib.util.module_from_spec(spec)
sys.modules["registers"] = R
spec.loader.exec_module(R)  # type: ignore[union-attr]


def build(p: str, power: str | None, energy: str | None, heat: str | None,
          cop_sensors: bool) -> dict:
    e = lambda domain, key: f"{domain}.{p}_{key}"  # noqa: E731
    s = lambda key: e("sensor", key)  # noqa: E731
    b = lambda key: e("binary_sensor", key)  # noqa: E731

    def heading(text: str, icon: str | None = None) -> dict:
        card = {"type": "heading", "heading": text, "heading_style": "title"}
        if icon:
            card["icon"] = icon
        return card

    def tile(entity: str, name: str | None = None, **kw) -> dict:
        card = {"type": "tile", "entity": entity, "vertical": False}
        if name:
            card["name"] = name
        card.update(kw)
        return card

    status_text = f"""{{% set comp = states('{s('compressor_frequency')}') | int(0) %}}
{{% if is_state('{b('fault')}', 'on') %}}Аварія
{{% elif is_state('{e('switch', 'power')}', 'off') %}}Вимкнено
{{% elif is_state('{b('defrost_active')}', 'on') %}}Розморожування
{{% elif is_state('{b('disinfection_active')}', 'on') %}}Дезінфекція
{{% elif comp > 0 and is_state('{b('dhw_3_way_valve')}', 'on') %}}Нагрів гарячої води
{{% elif comp > 0 and is_state('{s('operating_state')}', 'cooling') %}}Охолодження
{{% elif comp > 0 %}}Опалення
{{% else %}}Очікування{{% endif %}}"""
    status_color = f"""{{% set comp = states('{s('compressor_frequency')}') | int(0) %}}
{{% if is_state('{b('fault')}', 'on') %}}red
{{% elif is_state('{e('switch', 'power')}', 'off') %}}grey
{{% elif is_state('{b('defrost_active')}', 'on') %}}light-blue
{{% elif comp > 0 and is_state('{b('dhw_3_way_valve')}', 'on') %}}deep-orange
{{% elif comp > 0 and is_state('{s('operating_state')}', 'cooling') %}}blue
{{% elif comp > 0 %}}orange
{{% else %}}green{{% endif %}}"""
    status_card = {
        "type": "custom:mushroom-template-card",
        "primary": status_text,
        "secondary": (
            f"Режим: {{{{ state_translated('{e('select', 'operating_mode')}') }}}} · "
            f"Компресор {{{{ states('{s('compressor_frequency')}') }}}} Гц · "
            f"Вулиця {{{{ states('{s('outdoor_temperature')}') }}}} °C"
        ),
        "icon": "mdi:heat-pump",
        "icon_color": status_color,
        "entity": e("switch", "power"),
        "tap_action": {"action": "more-info"},
        "multiline_secondary": True,
        "fill_container": True,
        "grid_options": {"columns": 12},
    }

    def chip(entity: str, icon: str, on_color: str, content: str | None = None) -> dict:
        return {
            "type": "template",
            "entity": entity,
            "icon": icon,
            "icon_color": f"{{{{ '{on_color}' if is_state('{entity}', 'on') else 'disabled' }}}}",
            "content": content or f"{{{{ state_attr('{entity}', 'friendly_name') | replace('Тепловий насос ', '') }}}}",
            "tap_action": {"action": "more-info"},
        }

    chips = {
        "type": "custom:mushroom-chips-card",
        "alignment": "center",
        "grid_options": {"columns": 12},
        "chips": [
            {"type": "template", "entity": s("compressor_frequency"), "icon": "mdi:engine",
             "icon_color": f"{{{{ 'orange' if states('{s('compressor_frequency')}') | int(0) > 0 else 'disabled' }}}}",
             "content": f"{{{{ states('{s('compressor_frequency')}') }}}} Гц",
             "tap_action": {"action": "more-info"}},
            chip(b("main_circulation_pump"), "mdi:pump", "blue", "Насос"),
            chip(b("water_flow_detected"), "mdi:waves-arrow-right", "cyan", "Протік"),
            chip(b("dhw_3_way_valve"), "mdi:valve", "deep-orange", "Клапан ГВП"),
            chip(b("defrost_active"), "mdi:snowflake-melt", "light-blue", "Розморожування"),
            {"type": "template", "icon": "mdi:heating-coil",
             "icon_color": "{{ 'red' if " + " or ".join(
                 f"is_state('{b(k)}', 'on')" for k in (
                     "electric_heater_stage_1", "electric_heater_stage_2",
                     "hydrobox_electric_heater", "tank_electric_heater")) + " else 'disabled' }}",
             "content": "Тен"},
            chip(e("switch", "silent_mode"), "mdi:volume-off", "purple", "Тихий"),
        ],
    }

    fault_alert = {
        "type": "conditional",
        "conditions": [{"condition": "state", "entity": b("fault"), "state": "on"}],
        "card": {
            "type": "markdown",
            "content": (
                "## ⚠️ Аварія теплового насоса\n"
                f"{{% for f in state_attr('{s('active_faults')}', 'faults_uk') or [] %}}\n"
                "- **{{ f }}**\n{% endfor %}"
            ),
            "card_mod": {"style": "ha-card { border: 2px solid var(--error-color); }"},
        },
    }

    overview_state = {
        "type": "grid",
        "cards": [
            heading("Стан", "mdi:heat-pump"),
            status_card,
            fault_alert,
            chips,
            tile(e("switch", "power"), "Живлення", features=[{"type": "toggle"}],
                 features_position="inline"),
            tile(e("select", "operating_mode"), "Режим", features=[{"type": "select-options"}],
                 grid_options={"columns": 12}),
            tile(e("switch", "silent_mode"), "Тихий режим", features=[{"type": "toggle"}],
                 features_position="inline"),
            tile(e("switch", "weather_compensation"), "Погодна крива", features=[{"type": "toggle"}],
                 features_position="inline"),
        ],
    }
    overview_heating = {
        "type": "grid",
        "cards": [
            heading("Опалення", "mdi:radiator"),
            {"type": "thermostat", "entity": e("climate", "heating"), "name": "Опалення / охолодження",
             "features": [{"type": "climate-hvac-modes", "hvac_modes": ["off", "heat", "cool"]}]},
            tile(s("water_outlet_temperature"), "Подача"),
            tile(s("water_inlet_temperature"), "Зворот"),
            tile(s("buffer_tank_temperature"), "Буферний бак"),
            tile(s("water_delta_t"), "ΔT подача−зворот"),
            tile(s("current_temperature_target"), "Активна ціль"),
            tile(s("outdoor_temperature"), "Вулиця"),
        ],
    }
    overview_dhw = {
        "type": "grid",
        "cards": [
            heading("Гаряча вода", "mdi:water-boiler"),
            {"type": "thermostat", "entity": e("water_heater", "dhw"), "name": "Гаряча вода",
             "features": [{"type": "water-heater-operation-modes", "operation_modes": ["off", "heat_pump"]}]},
            tile(s("dhw_tank_temperature"), "Бак ГВП"),
            tile(b("dhw_3_way_valve"), "Клапан ГВП"),
            tile(e("switch", "disinfection"), "Дезінфекція", features=[{"type": "toggle"}],
                 features_position="inline"),
            tile(b("disinfection_active"), "Дезінфекція триває"),
        ],
    }

    energy_cards: list[dict] = [heading("Енергія та ефективність", "mdi:lightning-bolt")]
    if power:
        energy_cards.append(tile(power, "Споживання зараз"))
    if cop_sensors:
        energy_cards += [tile("sensor.hp_cop_daily", "COP сьогодні", icon="mdi:gauge"),
                         tile("sensor.hp_cop_monthly", "COP за місяць", icon="mdi:gauge"),
                         tile("sensor.hp_energy_daily", "Електрика сьогодні"),
                         tile("sensor.hp_heat_daily", "Тепло сьогодні")]
    energy_cards.append(tile(s("energy_consumption"), "Спожито всього (ТН)"))
    def daily_bars(title: str, series: list[tuple[str, str, str]]) -> dict:
        return {
            "type": "custom:apexcharts-card",
            "header": {"show": True, "title": title},
            "graph_span": "14d",
            "span": {"end": "day"},
            "apex_config": {"chart": {"height": 260}, "legend": {"show": True},
                            "plotOptions": {"bar": {"columnWidth": "70%"}}},
            "yaxis": [{"min": 0, "decimals": 0, "apex_config": {"title": {"text": "kWh"}}}],
            "series": [
                {"entity": ent, "name": name, "type": "column", "color": color,
                 "statistics": {"type": "change", "period": "day", "align": "start"},
                 "group_by": {"func": "last", "duration": "1d"}}
                for ent, name, color in series
            ],
            "grid_options": {"columns": 12},
        }

    if energy and heat:
        energy_cards.append(daily_bars("Електрика vs тепло по днях",
                                       [(energy, "Електрика", "#fbc02d"), (heat, "Тепло", "#ff7043")]))
    else:
        energy_cards.append(daily_bars("Спожита енергія по днях",
                                       [(s("energy_consumption"), "Електрика", "#fbc02d")]))
    overview_energy = {"type": "grid", "cards": energy_cards}

    temp_chart = {
        "type": "custom:apexcharts-card",
        "header": {"show": True, "title": "Температури та компресор (24 год)", "show_states": False},
        "graph_span": "24h",
        "apex_config": {"chart": {"height": 300}, "legend": {"show": True}, "stroke": {"width": 2}},
        "yaxis": [
            {"id": "t", "decimals": 0, "apex_config": {"title": {"text": "°C"}}},
            {"id": "hz", "opposite": True, "min": 0, "max": 120, "decimals": 0,
             "apex_config": {"title": {"text": "Гц"}}},
        ],
        "series": [
            {"entity": s("water_outlet_temperature"), "name": "Подача", "yaxis_id": "t", "color": "#ff7043",
             "group_by": {"func": "avg", "duration": "5min"}},
            {"entity": s("water_inlet_temperature"), "name": "Зворот", "yaxis_id": "t", "color": "#42a5f5",
             "group_by": {"func": "avg", "duration": "5min"}},
            {"entity": s("dhw_tank_temperature"), "name": "Бак ГВП", "yaxis_id": "t", "color": "#e53935",
             "group_by": {"func": "avg", "duration": "5min"}},
            {"entity": s("buffer_tank_temperature"), "name": "Буфер", "yaxis_id": "t", "color": "#ab47bc",
             "group_by": {"func": "avg", "duration": "5min"}},
            {"entity": s("outdoor_temperature"), "name": "Вулиця", "yaxis_id": "t", "color": "#66bb6a",
             "group_by": {"func": "avg", "duration": "5min"}},
            {"entity": s("compressor_frequency"), "name": "Компресор", "yaxis_id": "hz", "type": "area",
             "color": "#9e9e9e", "opacity": 0.25, "group_by": {"func": "avg", "duration": "5min"}},
        ],
        "grid_options": {"columns": "full"},
    }
    charts = {"type": "grid", "column_span": 3, "cards": [heading("Графіки", "mdi:chart-line"), temp_chart]}
    if power:
        charts["cards"].append({
            "type": "custom:apexcharts-card",
            "header": {"show": True, "title": "Споживана потужність (24 год)"},
            "graph_span": "24h",
            "apex_config": {"chart": {"height": 220}},
            "series": [{"entity": power, "name": "Потужність", "type": "area", "color": "#fbc02d",
                        "group_by": {"func": "avg", "duration": "5min"}}],
            "grid_options": {"columns": "full"},
        })

    overview = {
        "title": "Огляд", "path": "overview", "icon": "mdi:heat-pump", "type": "sections",
        "max_columns": 4,
        "sections": [overview_state, overview_heating, overview_dhw, overview_energy, charts],
    }

    # ---------------- Settings ----------------
    names = {d.key: d.uk for d in (R.SENSORS + R.DERIVED_SENSORS + R.BINARY_SENSORS + R.DERIVED_BINARY
                                   + R.NUMBERS + R.SELECTS + R.SWITCHES + R.BUTTONS)}

    def short(item: str | dict) -> str | dict:
        """Entities rows without the repeated device name prefix."""
        if isinstance(item, str):
            key = item.split(".", 1)[1].removeprefix(f"{p}_")
            if key in names:
                return {"entity": item, "name": names[key]}
        return item

    def entities_section(title: str, icon: str, items: list[str | dict]) -> dict:
        return {"type": "grid", "cards": [
            heading(title, icon),
            {"type": "entities", "entities": [short(i) for i in items], "state_color": True}]}

    n = lambda key: e("number", key)  # noqa: E731
    settings = {
        "title": "Налаштування", "path": "settings", "icon": "mdi:tune", "type": "sections",
        "max_columns": 3,
        "sections": [
            entities_section("Уставки", "mdi:thermometer", [
                n("heating_setpoint"), n("dhw_setpoint"), n("cooling_setpoint"),
                n("maximum_outlet_temperature"),
            ]),
            entities_section("Погодозалежна крива", "mdi:chart-bell-curve-cumulative", [
                e("switch", "weather_compensation"), n("curve_slope"), n("curve_offset"),
                {"type": "attribute", "entity": e("climate", "heating"), "attribute": "heating_setpoint",
                 "name": "Поточна уставка опалення", "suffix": "°C"},
            ]),
            entities_section("Пріоритети та гістерезиси", "mdi:swap-horizontal", [
                n("forced_dhw_time"), n("heating_restart_delta"), n("heating_standby_delta"),
                n("dhw_restart_delta"), n("dhw_standby_delta"),
            ]),
            entities_section("Насоси", "mdi:pump", [
                e("select", "circulation_pump_mode"), n("main_pump_interval"), n("main_pump_runtime"),
                e("select", "dhw_pump_mode"), e("switch", "manual_water_pump"),
            ]),
            entities_section("Електротен", "mdi:heating-coil", [
                e("select", "electric_heater_mode"), n("heater_on_ambient"), n("heater_delay"),
            ]),
            entities_section("Дезінфекція", "mdi:bacteria-outline", [
                e("switch", "disinfection"), n("disinfection_temperature"), n("disinfection_duration"),
                n("disinfection_start_hour"), n("disinfection_interval"),
            ]),
            {"type": "grid", "cards": [
                heading("Сервіс", "mdi:wrench"),
                {"type": "entities", "entities": [
                    short(e("switch", "silent_mode")), short(e("select", "temperature_control_source")),
                ]},
                {"type": "tile", "entity": e("button", "manual_defrost"), "name": "Примусове розморожування",
                 "icon": "mdi:snowflake-melt",
                 "tap_action": {"action": "perform-action", "perform_action": "button.press",
                                "target": {"entity_id": e("button", "manual_defrost")},
                                "confirmation": {
                                    "text": "Запустити примусове розморожування теплового насоса?"}}},
            ]},
        ],
    }

    # ---------------- Diagnostics ----------------
    fault_entities = [b(k) for _, _, k, _, _ in R.FAULT_BITS]
    diagnostics = {
        "title": "Діагностика", "path": "diagnostics", "icon": "mdi:stethoscope", "type": "sections",
        "max_columns": 3,
        "sections": [
            {"type": "grid", "cards": [
                heading("Аварії", "mdi:alert"),
                {"type": "conditional",
                 "conditions": [{"condition": "state", "entity": b("fault"), "state": "off"}],
                 "card": {"type": "markdown", "content": "✅ **Аварій немає.** Усі захисти в нормі."}},
                {"type": "entity-filter",
                 "conditions": [{"condition": "state", "state": "on"}],
                 "card": {"type": "entities", "title": "Активні аварії"}, "show_empty": False,
                 "entities": [short(x) for x in fault_entities]},
                {"type": "entities", "entities": [short(x) for x in (
                    s("active_faults"), b("alarm_output"), b("emergency_input"), s("firmware"))]},
            ]},
            entities_section("Холодильний контур", "mdi:snowflake-thermometer", [
                s("coil_temperature"), s("suction_temperature"), s("discharge_temperature"),
                s("distributor_tube_temperature"), s("antifreeze_temperature"), s("low_pressure"),
                s("eev_steps"), b("four_way_valve"),
            ]),
            entities_section("Компресор і вентилятори", "mdi:engine", [
                s("compressor_frequency"), s("compressor_target_frequency"), b("compressor_running"),
                s("fan_1_speed"), s("fan_2_speed"), b("fan_high_speed"), b("fan_low_speed"),
                s("compressor_starts"), s("compressor_runtime"),
            ]),
            entities_section("Електрика", "mdi:flash", [
                s("ac_input_voltage"), s("dc_bus_voltage"), s("compressor_phase_current"),
                s("ipm_temperature"), s("backup_heater_heating_runtime"), s("backup_heater_dhw_runtime"),
            ]),
            entities_section("Виходи (реле)", "mdi:electric-switch", [
                b("main_circulation_pump"), b("dhw_pump_running"), b("dhw_3_way_valve"),
                b("electric_heater_stage_1"), b("electric_heater_stage_2"), b("hydrobox_electric_heater"),
                b("tank_electric_heater"), b("crankcase_heater"), b("chassis_heater"),
                b("heat_pump_enabled"),
            ]),
            entities_section("Входи", "mdi:import", [
                b("water_flow_detected"), b("high_pressure_switch"), b("low_pressure_switch"),
                b("electric_heater_overload_input"), b("ac_mode_input"), b("dhw_mode_input"),
                b("ac_switch"), b("silent_mode_active"),
            ]),
            {"type": "grid", "column_span": 3, "cards": [
                heading("Холодильний контур (24 год)", "mdi:chart-line"),
                {"type": "history-graph", "hours_to_show": 24, "entities": [
                    s("discharge_temperature"), s("suction_temperature"), s("coil_temperature"),
                    s("outdoor_temperature")], "grid_options": {"columns": "full"}},
            ]},
        ],
    }
    return {"title": "Тепловий насос", "views": [overview, settings, diagnostics]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="hp")
    ap.add_argument("--power-meter")
    ap.add_argument("--energy-meter")
    ap.add_argument("--heat-meter")
    ap.add_argument("--cop-sensors", action="store_true",
                    help="include sensor.hp_cop_*/hp_energy_daily/hp_heat_daily (see README)")
    ap.add_argument("--json")
    ap.add_argument("--no-yaml", action="store_true")
    a = ap.parse_args()
    cfg = build(a.prefix, a.power_meter, a.energy_meter, a.heat_meter, a.cop_sensors)
    if a.json:
        Path(a.json).write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    if not a.no_yaml:
        import yaml  # noqa: PLC0415

        out = ROOT / "dashboard" / "heat_pump_dashboard.yaml"
        out.write_text("# Generated by scripts/build_dashboard.py – requires Mushroom & ApexCharts (HACS)\n"
                       + yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False, width=120),
                       encoding="utf-8")
        print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
