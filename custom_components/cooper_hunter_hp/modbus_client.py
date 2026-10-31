"""Minimal asyncio Modbus master (TCP, RTU-over-TCP, serial RTU).

Designed for gateways that are shared with other Modbus masters: responses that
do not belong to our request (foreign transaction id, slave, function code,
length or CRC) are silently skipped instead of being treated as errors.
"""

from __future__ import annotations

import asyncio
import logging
import random
import struct
import time
from typing import Any

_LOGGER = logging.getLogger(__name__)

TRANSPORT_TCP = "tcp"
TRANSPORT_RTU_OVER_TCP = "rtu_over_tcp"
TRANSPORT_SERIAL = "serial"

MAX_REGS_PER_READ = 125
READBACK_DELAY = 0.3  # seconds to let the controller apply a write before verifying


class ModbusError(Exception):
    """Communication error."""


class ModbusExceptionResponse(ModbusError):
    """Device answered with a Modbus exception."""

    def __init__(self, function: int, code: int) -> None:
        super().__init__(f"Modbus exception {code} for function {function}")
        self.function = function
        self.code = code


def crc16(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return struct.pack("<H", crc)


def _expected_pdu_len(pdu_request: bytes, first_bytes: bytes) -> int | None:
    """Return the full response PDU length (incl. function code) once known."""
    if len(first_bytes) < 1:
        return None
    function = first_bytes[0]
    if function & 0x80:
        return 2
    if function in (3, 4):
        if len(first_bytes) < 2:
            return None
        return 2 + first_bytes[1]
    if function in (6, 16):
        return 5
    return None


class ModbusClient:
    """Serialises all requests over one connection."""

    def __init__(
        self,
        transport: str,
        *,
        host: str | None = None,
        port: int | None = None,
        serial_port: str | None = None,
        baudrate: int = 9600,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        timeout: float = 3.0,
        retries: int = 3,
        request_delay: float = 0.05,
    ) -> None:
        self._transport = transport
        self._host = host
        self._port = port
        self._serial_port = serial_port
        self._serial_kwargs = {
            "baudrate": baudrate,
            "bytesize": bytesize,
            "parity": parity,
            "stopbits": stopbits,
        }
        self._timeout = timeout
        self._retries = retries
        self._request_delay = request_delay
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._tid = random.randint(1, 0x7FFF)
        self._last_request = 0.0

    @property
    def connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    async def connect(self) -> None:
        await self.close()
        try:
            if self._transport == TRANSPORT_SERIAL:
                import serial_asyncio_fast  # noqa: PLC0415

                self._reader, self._writer = await asyncio.wait_for(
                    serial_asyncio_fast.open_serial_connection(
                        url=self._serial_port, **self._serial_kwargs
                    ),
                    self._timeout,
                )
            else:
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(self._host, self._port), self._timeout
                )
        except (OSError, TimeoutError) as err:
            self._reader = self._writer = None
            raise ModbusError(f"Cannot connect: {err}") from err

    async def close(self) -> None:
        writer, self._writer, self._reader = self._writer, None, None
        if writer is not None:
            writer.close()
            try:
                await asyncio.wait_for(writer.wait_closed(), 2)
            except (OSError, TimeoutError):
                pass

    async def read_holding_registers(self, slave: int, address: int, count: int) -> list[int]:
        if not 1 <= count <= MAX_REGS_PER_READ:
            raise ValueError("count out of range")
        pdu = struct.pack(">BHH", 3, address, count)
        resp = await self._execute(slave, pdu, expected_data_len=2 * count)
        return [struct.unpack_from(">H", resp, 2 + 2 * i)[0] for i in range(count)]

    async def write_register(
        self, slave: int, address: int, value: int, *, verify: bool = True
    ) -> None:
        value &= 0xFFFF
        pdu = struct.pack(">BHH", 6, address, value)
        if not verify:
            await self._execute(slave, pdu)
            return
        # Some controllers (slow 9600 buses, or units that only answer on the
        # broadcast address 0) apply the write but drop or garble the echo.
        # Try once, and on failure confirm the write by reading the register
        # back before escalating to the full retry loop.
        try:
            await self._execute(slave, pdu, retries=0)
            return
        except ModbusError as first_err:
            if await self._readback_equals(slave, address, value):
                _LOGGER.debug(
                    "Write of %s to register %s got no valid echo (%r) but read-back matches",
                    value, address, first_err,
                )
                return
        try:
            await self._execute(slave, pdu)
        except ModbusError:
            if await self._readback_equals(slave, address, value):
                return
            raise

    async def _readback_equals(self, slave: int, address: int, value: int) -> bool:
        await asyncio.sleep(READBACK_DELAY)
        try:
            current = await self.read_holding_registers(slave, address, 1)
        except ModbusError:
            return False
        return current[0] == value

    async def write_registers(self, slave: int, address: int, values: list[int]) -> None:
        pdu = struct.pack(">BHHB", 16, address, len(values), 2 * len(values)) + b"".join(
            struct.pack(">H", v & 0xFFFF) for v in values
        )
        await self._execute(slave, pdu)

    async def _execute(
        self,
        slave: int,
        pdu: bytes,
        expected_data_len: int | None = None,
        retries: int | None = None,
    ) -> bytes:
        last_err: Exception | None = None
        if retries is None:
            retries = self._retries
        async with self._lock:
            for attempt in range(retries + 1):
                try:
                    if not self.connected:
                        await self.connect()
                    wait = self._request_delay - (time.monotonic() - self._last_request)
                    if wait > 0:
                        await asyncio.sleep(wait)
                    try:
                        resp = await asyncio.wait_for(
                            self._transceive(slave, pdu, expected_data_len), self._timeout
                        )
                    finally:
                        self._last_request = time.monotonic()
                    if resp[0] & 0x80:
                        raise ModbusExceptionResponse(resp[0] & 0x7F, resp[1])
                    return resp
                except ModbusExceptionResponse:
                    raise
                except (OSError, TimeoutError, asyncio.IncompleteReadError, ModbusError) as err:
                    last_err = err
                    _LOGGER.debug(
                        "Modbus request %s to slave %s failed (attempt %s): %r",
                        pdu.hex(), slave, attempt + 1, err,
                    )
                    # Drop the connection so stale/foreign bytes are not mixed into the next answer.
                    await self.close()
        raise ModbusError(f"Request failed after {retries + 1} attempts: {last_err!r}")

    async def _transceive(self, slave: int, pdu: bytes, expected_data_len: int | None) -> bytes:
        assert self._reader is not None and self._writer is not None
        function = pdu[0]
        if self._transport == TRANSPORT_TCP:
            self._tid = (self._tid % 0xFFFF) + 1
            tid = self._tid
            self._writer.write(struct.pack(">HHHB", tid, 0, len(pdu) + 1, slave) + pdu)
            await self._writer.drain()
            while True:
                header = await self._reader.readexactly(7)
                r_tid, proto, length, unit = struct.unpack(">HHHB", header)
                if length < 2 or length > 260:
                    raise ModbusError("Corrupted MBAP header")
                body = await self._reader.readexactly(length - 1)
                if r_tid != tid or proto != 0 or unit != slave:
                    continue  # answer to another master sharing the gateway
                if not self._pdu_matches(body, pdu, expected_data_len):
                    continue
                return body

        frame = bytes([slave]) + pdu
        self._writer.write(frame + crc16(frame))
        await self._writer.drain()
        buf = b""
        while True:
            buf += await self._reader.read(256)
            while len(buf) >= 5:
                if buf[0] != slave or (buf[1] & 0x7F) != function:
                    buf = buf[1:]
                    continue
                total = _expected_pdu_len(pdu, buf[1:3])
                if total is None:
                    break
                total += 3  # slave + crc
                if len(buf) < total:
                    break
                candidate = buf[:total]
                if crc16(candidate[:-2]) != candidate[-2:]:
                    buf = buf[1:]
                    continue
                body = candidate[1:-2]
                if self._pdu_matches(body, pdu, expected_data_len):
                    return body
                buf = buf[total:]

    @staticmethod
    def _pdu_matches(body: bytes, pdu: bytes, expected_data_len: int | None) -> bool:
        function = pdu[0]
        if not body:
            return False
        if body[0] == function | 0x80:
            return len(body) >= 2
        if body[0] != function:
            return False
        if function in (3, 4):
            return len(body) >= 2 and body[1] == expected_data_len and len(body) == 2 + body[1]
        # Write responses echo the address (+ value / quantity). Match on the
        # address only: some controllers echo the clamped/rounded value.
        return len(body) >= 3 and body[1:3] == pdu[1:3]

    def describe(self) -> dict[str, Any]:
        return {
            "transport": self._transport,
            "host": self._host,
            "port": self._port,
            "serial_port": self._serial_port,
        }
