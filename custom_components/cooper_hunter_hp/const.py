"""Constants for the Cooper&Hunter heat pump integration."""

from __future__ import annotations

DOMAIN = "cooper_hunter_hp"
MANUFACTURER = "Cooper&Hunter"
DEFAULT_MODEL = "CH-HP15UIMPZM"

CONF_TRANSPORT = "transport"
CONF_SLAVE = "slave"
CONF_SERIAL_PORT = "serial_port"
CONF_BAUDRATE = "baudrate"
CONF_PARITY = "parity"
CONF_STOPBITS = "stopbits"
CONF_MODEL = "model"
CONF_ENTITY_PREFIX = "entity_prefix"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_PARAM_INTERVAL = "parameter_interval"

DEFAULT_PORT = 502
DEFAULT_SLAVE = 1
DEFAULT_BAUDRATE = 9600
DEFAULT_PREFIX = "hp"
DEFAULT_SCAN_INTERVAL = 10
DEFAULT_PARAM_INTERVAL = 60
# Consecutive failed polls tolerated (stale data kept) before entities go unavailable.
MAX_STALE_POLLS = 3

# Each controller page is 90 registers; the first 10 are a header
# (ASCII firmware id in +0..+5, 0x0210 in +8, page start address in +9).
PAGE_HEADER_LEN = 10
FIRMWARE_REGS = (0, 6)

# (start, count) blocks read from the controller.
PARAM_BLOCKS: tuple[tuple[int, int], ...] = ((1001, 90), (1091, 90), (1181, 90))
STATUS_BLOCKS: tuple[tuple[int, int], ...] = ((2001, 90), (2091, 55))
# Pages that newer firmware exposes (EMS / "allow disinfection in standby").
# Read best-effort: skipped permanently after OPTIONAL_BLOCK_MAX_FAILURES misses.
OPTIONAL_PARAM_BLOCKS: tuple[tuple[int, int], ...] = ((1361, 90),)
OPTIONAL_BLOCK_MAX_FAILURES = 3

SENSOR_FAULT_VALUE = 32767
