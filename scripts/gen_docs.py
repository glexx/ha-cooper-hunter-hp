"""Generate docs/REGISTERS.md from registers.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "registers", ROOT / "custom_components" / "cooper_hunter_hp" / "registers.py")
R = importlib.util.module_from_spec(spec)
sys.modules["registers"] = R
spec.loader.exec_module(R)  # type: ignore[union-attr]

SCALE = {"temp": "×0.1 (signed)", "d5": "×0.1", "d9": "×0.01", "u32": "32-bit (H,L)", "u16": "×1",
         "s16": "×1 (signed)", "enum": "enum"}


def opts(options) -> str:
    return ", ".join(f"{k}={v[1]}" for k, v in options.items()) if options else ""


def main() -> None:
    out = ["# Register map (holding registers, FC03 read / FC06 write)", "",
           "Generated from `custom_components/cooper_hunter_hp/registers.py`. "
           "Controller pages: 1001–1090, 1091–1180, 1181–1270 (parameters), 2001–2090, 2091–2180 (status); "
           "the first 10 registers of every page are a header (firmware id, page start address).", "",
           "System clock: 1250 enable, 1251 minute, 1252 hour, 1253 day, 1254 month, 1255 year (2000+N). "
           "The controller schedules legionella disinfection itself (registers 1152–1156) and never runs it "
           "while the clock is unset, so the integration keeps these registers in sync with Home Assistant "
           "time automatically.", ""]
    out += ["## Writable", "", "| Address | Entity | Type / scale | Range / options | Name |",
            "|---|---|---|---|---|"]
    rows = []
    for d in R.SWITCHES:
        rows.append((d.address, f"switch.{d.key}", "u16", f"{d.off}/{d.on}", d.en))
    for d in R.SELECTS:
        rows.append((d.address, f"select.{d.key}", "enum", opts(d.options), d.en))
    for d in R.NUMBERS:
        rows.append((d.address, f"number.{d.key}", SCALE.get(d.dtype, d.dtype),
                     f"{d.min}…{d.max} {d.unit or ''}".strip(), d.en))
    for d in R.BUTTONS:
        rows.append((d.address, f"button.{d.key}", f"bit {d.bit}", "", d.en))
    out += [f"| {a} | `{e}` | {t} | {r} | {n} |" for a, e, t, r, n in sorted(rows)]
    out += ["", "## Read-only", "", "| Address | Entity | Type / scale | Unit / options | Name |",
            "|---|---|---|---|---|"]
    rows = [(d.address, f"sensor.{d.key}", SCALE.get(d.dtype, d.dtype), d.unit or opts(d.options), d.en)
            for d in R.SENSORS]
    out += [f"| {a} | `{e}` | {t} | {u} | {n} |" for a, e, t, u, n in sorted(rows)]
    out += ["", "## Bits", "", "| Register | Bit | Entity | Name |", "|---|---|---|---|"]
    bits = [(d.address, d.bit if d.bit is not None else f"=={d.equals}", f"binary_sensor.{d.key}",
             d.en + (" (inverted)" if d.invert else "")) for d in R.BINARY_SENSORS]
    out += [f"| {a} | {b} | `{e}` | {n} |" for a, b, e, n in sorted(bits, key=lambda x: (x[0], str(x[1])))]
    (ROOT / "docs" / "REGISTERS.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("wrote docs/REGISTERS.md")


if __name__ == "__main__":
    main()
