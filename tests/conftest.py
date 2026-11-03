"""Test fixtures: an in-process Modbus TCP slave serving a real register snapshot."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import struct

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"

SNAPSHOT = {int(k): v for k, v in json.loads(
    (Path(__file__).parent / "fixtures_registers.json").read_text()).items()}


class FakeSlave:
    """Minimal Modbus TCP server; also emits foreign frames to mimic a shared gateway."""

    def __init__(self, registers: dict[int, int], slave: int = 1) -> None:
        self.registers = dict(registers)
        self.slave = slave
        self.writes: list[tuple[int, int]] = []
        self.unanswered: list[tuple[int, int]] = []
        self.noise = True
        self.server: asyncio.base_events.Server | None = None
        self.port = 0
        self._writers: set[asyncio.StreamWriter] = set()

    async def start(self) -> None:
        self.server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]

    async def stop(self) -> None:
        if self.server:
            self.server.close()
            for writer in list(self._writers):
                writer.close()
            await asyncio.wait_for(self.server.wait_closed(), 5)

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self._writers.add(writer)
        try:
            while True:
                header = await reader.readexactly(7)
                tid, _proto, length, unit = struct.unpack(">HHHB", header)
                pdu = await reader.readexactly(length - 1)
                if self.noise:
                    # Answer for another master (different tid & unit) first.
                    foreign = struct.pack(">BBH", 3, 2, 0x1234)
                    writer.write(struct.pack(">HHHB", (tid + 7) & 0xFFFF, 0, len(foreign) + 1, 4) + foreign)
                if unit != self.slave:
                    continue
                resp = self._process(pdu)
                if resp is None:
                    continue
                writer.write(struct.pack(">HHHB", tid, 0, len(resp) + 1, unit) + resp)
                await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionError):
            pass
        finally:
            self._writers.discard(writer)
            writer.close()

    def _process(self, pdu: bytes) -> bytes | None:
        fc = pdu[0]
        if fc == 3:
            addr, count = struct.unpack(">HH", pdu[1:5])
            if any(a not in self.registers for a in range(addr, addr + count)):
                self.unanswered.append((addr, count))
                return None  # like the real controller: no answer
            data = b"".join(struct.pack(">H", self.registers[a]) for a in range(addr, addr + count))
            return bytes([3, len(data)]) + data
        if fc == 6:
            addr, value = struct.unpack(">HH", pdu[1:5])
            self.registers[addr] = value
            self.writes.append((addr, value))
            return pdu
        if fc == 16:
            addr, count = struct.unpack(">HH", pdu[1:5])
            for i in range(count):
                value = struct.unpack(">H", pdu[6 + 2 * i:8 + 2 * i])[0]
                self.registers[addr + i] = value
                self.writes.append((addr + i, value))
            return pdu[:5]
        return bytes([fc | 0x80, 1])


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
async def fake_slave(socket_enabled):
    slave = FakeSlave(SNAPSHOT)
    await slave.start()
    yield slave
    await slave.stop()
