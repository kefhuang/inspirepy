# inspirepy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python library that provides full control of the Inspire-Robots RH56 Dexterous Hand over USB serial.

**Architecture:** A layered design with protocol (packet framing/checksum) at the bottom, registers (address map) above it, and the user-facing Hand/Finger objects on top. Config and sequence persistence use YAML files on the host machine.

**Tech Stack:** Python 3, pyserial, pyyaml, pytest

---

## File Structure

| File | Responsibility |
|------|---------------|
| `inspirepy/__init__.py` | Public exports: `InspireHand` |
| `inspirepy/constants.py` | Enums (`Status`, `ErrorFlag`, `FingerName`, `BaudRate`), DOF-to-finger mapping, joint limits |
| `inspirepy/registers.py` | Register address constants, register metadata (address, length, type, R/W) |
| `inspirepy/protocol.py` | Build request packets, parse response packets, checksum calculation |
| `inspirepy/finger.py` | `Finger` class: per-finger control methods and sensor properties |
| `inspirepy/hand.py` | `InspireHand` class: connection, bulk ops, system commands, config, sequences |
| `inspirepy/sequence.py` | `ActionSequence` class: step builder, upload/run/save/load |
| `tests/test_constants.py` | Tests for enums and mappings |
| `tests/test_registers.py` | Tests for register addresses and metadata |
| `tests/test_protocol.py` | Tests for packet building, parsing, checksum |
| `tests/test_finger.py` | Tests for Finger class with mocked protocol |
| `tests/test_hand.py` | Tests for InspireHand class with mocked protocol |
| `tests/test_sequence.py` | Tests for ActionSequence class |
| `tests/test_config.py` | Tests for YAML config save/load |
| `pyproject.toml` | Package metadata, dependencies |

---

### Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `inspirepy/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "inspirepy"
version = "0.1.0"
description = "Python library for the Inspire-Robots RH56 Dexterous Hand"
requires-python = ">=3.9"
dependencies = [
    "pyserial>=3.5",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
]
```

- [ ] **Step 2: Create inspirepy/__init__.py**

```python
from inspirepy.hand import InspireHand

__all__ = ["InspireHand"]
```

- [ ] **Step 3: Create tests/__init__.py**

Empty file.

- [ ] **Step 4: Install package in dev mode and verify**

Run: `cd /home/kefhuang/Development/inspirepy && pip install -e ".[dev]"`
Expected: Successful install with pyserial, pyyaml, pytest available.

- [ ] **Step 5: Commit**

```bash
git init
git add pyproject.toml inspirepy/__init__.py tests/__init__.py
git commit -m "chore: scaffold inspirepy project with dependencies"
```

---

### Task 2: Constants and enums

**Files:**
- Create: `inspirepy/constants.py`
- Create: `tests/test_constants.py`

- [ ] **Step 1: Write tests for constants**

```python
# tests/test_constants.py
from inspirepy.constants import (
    Status,
    ErrorFlag,
    FingerName,
    BaudRate,
    FINGER_NAMES,
    JOINT_LIMITS,
    NUM_DOFS,
)


def test_status_values():
    assert Status.UNCLENCHING == 0
    assert Status.GRASPING == 1
    assert Status.TARGET_REACHED == 2
    assert Status.FORCE_LIMIT_REACHED == 3
    assert Status.CURRENT_PROTECTION == 5
    assert Status.LOCKED_ROTOR == 6
    assert Status.ACTUATOR_FAULT == 7


def test_error_flag_bits():
    assert ErrorFlag.LOCKED_ROTOR == 0x01
    assert ErrorFlag.OVER_TEMP == 0x02
    assert ErrorFlag.OVER_CURRENT == 0x04
    assert ErrorFlag.ABNORMAL_OPERATION == 0x08
    assert ErrorFlag.COMMUNICATION == 0x10


def test_finger_names_order():
    assert FINGER_NAMES == [
        "little", "ring", "middle", "index", "thumb_bend", "thumb_rotation"
    ]


def test_num_dofs():
    assert NUM_DOFS == 6


def test_baud_rate_mapping():
    assert BaudRate.B115200 == 0
    assert BaudRate.B57600 == 1
    assert BaudRate.B19200 == 2


def test_joint_limits_structure():
    assert len(JOINT_LIMITS) == 6
    for name in FINGER_NAMES:
        limits = JOINT_LIMITS[name]
        assert "min_deg" in limits
        assert "max_deg" in limits
        assert "angle_range" in limits
        assert limits["angle_range"] == (0, 1000)


def test_joint_limits_values():
    assert JOINT_LIMITS["little"]["min_deg"] == 19.0
    assert JOINT_LIMITS["little"]["max_deg"] == 176.7
    assert JOINT_LIMITS["thumb_bend"]["min_deg"] == -13.0
    assert JOINT_LIMITS["thumb_bend"]["max_deg"] == 53.6
    assert JOINT_LIMITS["thumb_rotation"]["min_deg"] == 90.0
    assert JOINT_LIMITS["thumb_rotation"]["max_deg"] == 165.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/kefhuang/Development/inspirepy && pytest tests/test_constants.py -v`
Expected: FAIL — cannot import from `inspirepy.constants`

- [ ] **Step 3: Implement constants.py**

```python
# inspirepy/constants.py
from enum import IntEnum


NUM_DOFS = 6

FINGER_NAMES = [
    "little", "ring", "middle", "index", "thumb_bend", "thumb_rotation"
]


class Status(IntEnum):
    UNCLENCHING = 0
    GRASPING = 1
    TARGET_REACHED = 2
    FORCE_LIMIT_REACHED = 3
    CURRENT_PROTECTION = 5
    LOCKED_ROTOR = 6
    ACTUATOR_FAULT = 7


class ErrorFlag(IntEnum):
    LOCKED_ROTOR = 0x01
    OVER_TEMP = 0x02
    OVER_CURRENT = 0x04
    ABNORMAL_OPERATION = 0x08
    COMMUNICATION = 0x10


class BaudRate(IntEnum):
    B115200 = 0
    B57600 = 1
    B19200 = 2


BAUD_RATE_VALUES = {
    BaudRate.B115200: 115200,
    BaudRate.B57600: 57600,
    BaudRate.B19200: 19200,
}

BAUD_RATE_LOOKUP = {v: k for k, v in BAUD_RATE_VALUES.items()}


JOINT_LIMITS = {
    "little":         {"min_deg": 19.0,  "max_deg": 176.7, "angle_range": (0, 1000)},
    "ring":           {"min_deg": 19.0,  "max_deg": 176.7, "angle_range": (0, 1000)},
    "middle":         {"min_deg": 19.0,  "max_deg": 176.7, "angle_range": (0, 1000)},
    "index":          {"min_deg": 19.0,  "max_deg": 176.7, "angle_range": (0, 1000)},
    "thumb_bend":     {"min_deg": -13.0, "max_deg": 53.6,  "angle_range": (0, 1000)},
    "thumb_rotation": {"min_deg": 90.0,  "max_deg": 165.0, "angle_range": (0, 1000)},
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/kefhuang/Development/inspirepy && pytest tests/test_constants.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add inspirepy/constants.py tests/test_constants.py
git commit -m "feat: add constants, enums, and joint limits"
```

---

### Task 3: Register map

**Files:**
- Create: `inspirepy/registers.py`
- Create: `tests/test_registers.py`

- [ ] **Step 1: Write tests for register map**

```python
# tests/test_registers.py
from inspirepy.registers import Register, REGISTERS


def test_hand_id_register():
    r = REGISTERS["HAND_ID"]
    assert r.address == 1000
    assert r.length == 1
    assert r.writable is True


def test_angle_set_register():
    r = REGISTERS["ANGLE_SET"]
    assert r.address == 1486
    assert r.length == 12
    assert r.writable is True


def test_angle_act_register():
    r = REGISTERS["ANGLE_ACT"]
    assert r.address == 1546
    assert r.length == 12
    assert r.writable is False


def test_pos_set_register():
    r = REGISTERS["POS_SET"]
    assert r.address == 1474
    assert r.length == 12
    assert r.writable is True


def test_temp_register():
    r = REGISTERS["TEMP"]
    assert r.address == 1618
    assert r.length == 6
    assert r.writable is False


def test_error_register():
    r = REGISTERS["ERROR"]
    assert r.address == 1606
    assert r.length == 6
    assert r.writable is False


def test_status_register():
    r = REGISTERS["STATUS"]
    assert r.address == 1612
    assert r.length == 6
    assert r.writable is False


def test_voltage_register():
    r = REGISTERS["VLTAGE"]
    assert r.address == 1472
    assert r.length == 2
    assert r.writable is False


def test_action_seq_step_registers():
    for i in range(8):
        r = REGISTERS[f"ACTION_SEQ_STEP_{i}"]
        assert r.address == 2016 + i * 38
        assert r.length == 38
        assert r.writable is True


def test_action_seq_control_registers():
    assert REGISTERS["ACTION_SEQ_INDEX"].address == 2320
    assert REGISTERS["ACTION_SEQ_RUN"].address == 2322
    assert REGISTERS["SAVE_ACTION_SEQ"].address == 2321
    assert REGISTERS["ACTION_SEQ_STEPNUM"].address == 2002
    assert REGISTERS["ACTION_SEQ_CHECK_DATA1"].address == 2000
    assert REGISTERS["ACTION_SEQ_CHECK_DATA2"].address == 2001


def test_all_registers_have_required_fields():
    for name, r in REGISTERS.items():
        assert isinstance(r.address, int), f"{name} missing address"
        assert isinstance(r.length, int), f"{name} missing length"
        assert isinstance(r.writable, bool), f"{name} missing writable"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/kefhuang/Development/inspirepy && pytest tests/test_registers.py -v`
Expected: FAIL — cannot import from `inspirepy.registers`

- [ ] **Step 3: Implement registers.py**

```python
# inspirepy/registers.py
from dataclasses import dataclass


@dataclass(frozen=True)
class Register:
    address: int
    length: int  # in bytes
    writable: bool


REGISTERS = {
    # System
    "HAND_ID":               Register(1000, 1, True),
    "REDU_RATIO":            Register(1002, 1, True),
    "CLEAR_ERROR":           Register(1004, 1, True),
    "SAVE":                  Register(1005, 1, True),
    "RESET_PARA":            Register(1006, 1, True),
    "GESTURE_FORCE_CLB":     Register(1009, 1, True),

    # Per-DOF config (6 x short = 12 bytes)
    "CURRENT_LIMIT":         Register(1020, 12, True),
    "DEFAULT_SPEED_SET":     Register(1032, 12, True),
    "DEFAULT_FORCE_SET":     Register(1044, 12, True),

    # Read-only system
    "VLTAGE":                Register(1472, 2, False),

    # Per-DOF control (6 x short = 12 bytes)
    "POS_SET":               Register(1474, 12, True),
    "ANGLE_SET":             Register(1486, 12, True),
    "FORCE_SET":             Register(1498, 12, True),
    "SPEED_SET":             Register(1522, 12, True),

    # Per-DOF sensors (6 x short = 12 bytes)
    "POS_ACT":               Register(1534, 12, False),
    "ANGLE_ACT":             Register(1546, 12, False),
    "FORCE_ACT":             Register(1582, 12, False),
    "CURRENT":               Register(1594, 12, False),

    # Per-DOF sensors (6 x byte = 6 bytes)
    "ERROR":                 Register(1606, 6, False),
    "STATUS":                Register(1612, 6, False),
    "TEMP":                  Register(1618, 6, False),

    # Action sequence control
    "ACTION_SEQ_CHECK_DATA1": Register(2000, 1, True),
    "ACTION_SEQ_CHECK_DATA2": Register(2001, 1, True),
    "ACTION_SEQ_STEPNUM":     Register(2002, 1, True),
    "ACTION_SEQ_INDEX":       Register(2320, 1, True),
    "SAVE_ACTION_SEQ":        Register(2321, 1, True),
    "ACTION_SEQ_RUN":         Register(2322, 1, True),
    "ACTION_ADJUST_FORCE_SET": Register(2324, 2, True),
}

# Action sequence step registers (8 steps, 19 shorts = 38 bytes each)
for _i in range(8):
    REGISTERS[f"ACTION_SEQ_STEP_{_i}"] = Register(2016 + _i * 38, 38, True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/kefhuang/Development/inspirepy && pytest tests/test_registers.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add inspirepy/registers.py tests/test_registers.py
git commit -m "feat: add register address map"
```

---

### Task 4: Protocol layer

**Files:**
- Create: `inspirepy/protocol.py`
- Create: `tests/test_protocol.py`

- [ ] **Step 1: Write tests for protocol**

```python
# tests/test_protocol.py
from unittest.mock import MagicMock, call
from inspirepy.protocol import Protocol


def make_protocol(response_bytes=b""):
    serial_mock = MagicMock()
    serial_mock.read.return_value = response_bytes
    proto = Protocol(serial_mock)
    return proto, serial_mock


def test_checksum_calculation():
    proto, _ = make_protocol()
    # Checksum is low byte of sum of all bytes
    assert proto._checksum(bytes([0x01, 0x04, 0x11, 0x0A, 0x06, 0x0C])) == 0x32


def test_build_read_packet():
    proto, _ = make_protocol()
    # Read ANGLE_ACT (address=1546=0x060A, length=12=0x0C) for hand_id=1
    packet = proto._build_read_packet(hand_id=1, address=1546, length=12)
    assert packet[0] == 0xEB  # header
    assert packet[1] == 0x90  # header
    assert packet[2] == 0x01  # hand_id
    assert packet[3] == 0x04  # frame data length
    assert packet[4] == 0x11  # read flag
    assert packet[5] == 0x0A  # address low byte
    assert packet[6] == 0x06  # address high byte
    assert packet[7] == 0x0C  # register length
    assert packet[8] == proto._checksum(packet[2:8])


def test_build_write_packet():
    proto, _ = make_protocol()
    # Write single byte (value=1) to RESET_PARA (address=1006=0x03EE) for hand_id=1
    data = bytes([0x01])
    packet = proto._build_write_packet(hand_id=1, address=1006, data=data)
    assert packet[0] == 0xEB
    assert packet[1] == 0x90
    assert packet[2] == 0x01  # hand_id
    assert packet[3] == 0x04  # frame data length: len(data) + 3
    assert packet[4] == 0x12  # write flag
    assert packet[5] == 0xEE  # address low byte (1006 & 0xFF)
    assert packet[6] == 0x03  # address high byte (1006 >> 8)
    assert packet[7] == 0x01  # data
    assert packet[8] == proto._checksum(packet[2:8])


def test_build_write_packet_multi_byte():
    proto, _ = make_protocol()
    # Write 12 bytes (6 shorts) to ANGLE_SET (address=1486=0x05CE) for hand_id=1
    # Values: [100, 100, 100, 100, 1000, 0] as little-endian shorts
    import struct
    data = struct.pack("<6h", 100, 100, 100, 100, 1000, 0)
    packet = proto._build_write_packet(hand_id=1, address=1486, data=data)
    assert packet[0] == 0xEB
    assert packet[1] == 0x90
    assert packet[2] == 0x01
    assert packet[3] == 15  # 12 + 3
    assert packet[4] == 0x12
    assert packet[5] == 0xCE  # address low
    assert packet[6] == 0x05  # address high
    assert len(packet) == 2 + 1 + 1 + 1 + 2 + 12 + 1  # header(2) + id + len + flag + addr(2) + data(12) + checksum


def test_parse_read_response():
    proto, _ = make_protocol()
    # Response for reading ANGLE_ACT with all angles = 100 (0x0064)
    # Header: 0x90 0xEB, id=1, len=15 (12+3), flag=0x11, addr_l=0x0A, addr_h=0x06
    # 6 shorts of 100 = 0x6400 each (little-endian)
    response = bytes([
        0x90, 0xEB,  # response header
        0x01,        # hand_id
        0x0F,        # length: 12 + 3
        0x11,        # read response flag
        0x0A, 0x06,  # address
        0x64, 0x00, 0x64, 0x00, 0x64, 0x00,  # 100, 100, 100
        0x64, 0x00, 0x64, 0x00, 0x64, 0x00,  # 100, 100, 100
    ])
    checksum = proto._checksum(response[2:-0] if False else response[2:])
    response = response + bytes([checksum])
    data = proto._parse_response(response)
    assert data == bytes([0x64, 0x00] * 6)


def test_parse_write_response():
    proto, _ = make_protocol()
    # Write ack: header 0x90 0xEB, id=1, len=4, flag=0x12, addr_l, addr_h, 0x01, checksum
    response = bytes([
        0x90, 0xEB,
        0x01,        # hand_id
        0x04,        # length
        0x12,        # write response flag
        0xCE, 0x05,  # address
        0x01,        # success
    ])
    checksum = proto._checksum(response[2:])
    response = response + bytes([checksum])
    data = proto._parse_response(response)
    assert data == bytes([0x01])


def test_read_register_sends_and_receives():
    proto, serial_mock = make_protocol()
    # Build the expected response for reading 1 byte from HAND_ID
    response = bytes([
        0x90, 0xEB,
        0x01,  # hand_id
        0x04,  # length: 1 + 3
        0x11,  # read flag
        0xE8, 0x03,  # address 1000
        0x01,  # data: id=1
    ])
    checksum = proto._checksum(response[2:])
    response = response + bytes([checksum])
    serial_mock.read.return_value = response

    result = proto.read_register(hand_id=1, address=1000, length=1)
    serial_mock.write.assert_called_once()
    assert result == bytes([0x01])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/kefhuang/Development/inspirepy && pytest tests/test_protocol.py -v`
Expected: FAIL — cannot import `Protocol`

- [ ] **Step 3: Implement protocol.py**

```python
# inspirepy/protocol.py
import struct

REQUEST_HEADER = bytes([0xEB, 0x90])
RESPONSE_HEADER = bytes([0x90, 0xEB])
READ_FLAG = 0x11
WRITE_FLAG = 0x12


class Protocol:
    def __init__(self, serial_port):
        self._serial = serial_port

    def _checksum(self, data: bytes) -> int:
        return sum(data) & 0xFF

    def _build_read_packet(self, hand_id: int, address: int, length: int) -> bytes:
        addr_l = address & 0xFF
        addr_h = (address >> 8) & 0xFF
        frame_data = bytes([hand_id, 0x04, READ_FLAG, addr_l, addr_h, length])
        cs = self._checksum(frame_data)
        return REQUEST_HEADER + frame_data + bytes([cs])

    def _build_write_packet(self, hand_id: int, address: int, data: bytes) -> bytes:
        addr_l = address & 0xFF
        addr_h = (address >> 8) & 0xFF
        frame_len = len(data) + 3
        frame_data = bytes([hand_id, frame_len, WRITE_FLAG, addr_l, addr_h]) + data
        cs = self._checksum(frame_data)
        return REQUEST_HEADER + frame_data + bytes([cs])

    def _parse_response(self, response: bytes) -> bytes:
        if len(response) < 5:
            raise ValueError(f"Response too short: {len(response)} bytes")
        if response[0:2] != RESPONSE_HEADER:
            raise ValueError(f"Invalid response header: {response[0:2].hex()}")
        frame_len = response[3]
        expected_checksum = self._checksum(response[2:-1])
        actual_checksum = response[-1]
        if expected_checksum != actual_checksum:
            raise ValueError(
                f"Checksum mismatch: expected {expected_checksum:#x}, got {actual_checksum:#x}"
            )
        # Data starts after header(2) + id(1) + len(1) + flag(1) + addr(2) = byte 7
        return response[7:-1]

    def read_register(self, hand_id: int, address: int, length: int) -> bytes:
        packet = self._build_read_packet(hand_id, address, length)
        self._serial.write(packet)
        # Response: header(2) + id(1) + len(1) + flag(1) + addr(2) + data(length) + checksum(1)
        response_len = 2 + 1 + 1 + 1 + 2 + length + 1
        response = self._serial.read(response_len)
        return self._parse_response(response)

    def write_register(self, hand_id: int, address: int, data: bytes) -> bytes:
        packet = self._build_write_packet(hand_id, address, data)
        self._serial.write(packet)
        # Write ack: header(2) + id(1) + len(1) + flag(1) + addr(2) + status(1) + checksum(1)
        response_len = 9
        response = self._serial.read(response_len)
        return self._parse_response(response)

    def write_shorts(self, hand_id: int, address: int, values: list[int]) -> bytes:
        data = struct.pack(f"<{len(values)}h", *values)
        return self.write_register(hand_id, address, data)

    def read_shorts(self, hand_id: int, address: int, count: int) -> list[int]:
        raw = self.read_register(hand_id, address, count * 2)
        return list(struct.unpack(f"<{count}h", raw))

    def read_bytes(self, hand_id: int, address: int, count: int) -> list[int]:
        raw = self.read_register(hand_id, address, count)
        return list(raw)

    def write_byte(self, hand_id: int, address: int, value: int) -> bytes:
        return self.write_register(hand_id, address, bytes([value]))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/kefhuang/Development/inspirepy && pytest tests/test_protocol.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add inspirepy/protocol.py tests/test_protocol.py
git commit -m "feat: add serial protocol layer (packet build/parse/checksum)"
```

---

### Task 5: Finger class

**Files:**
- Create: `inspirepy/finger.py`
- Create: `tests/test_finger.py`

- [ ] **Step 1: Write tests for Finger**

```python
# tests/test_finger.py
import struct
from unittest.mock import MagicMock, call
from inspirepy.finger import Finger
from inspirepy.constants import Status, JOINT_LIMITS


def make_finger(dof_index=3, name="index"):
    proto = MagicMock()
    finger = Finger(protocol=proto, hand_id=1, dof_index=dof_index, name=name)
    return finger, proto


def test_set_angle_absolute():
    finger, proto = make_finger()
    finger.set_angle(500)
    # Should write to ANGLE_SET at address 1486, but only for this DOF
    # DOF 3 = index: address offset = 3 * 2 = 6, so address = 1486 + 6 = 1492
    proto.write_shorts.assert_called_with(1, 1492, [500])


def test_set_angle_with_speed():
    finger, proto = make_finger()
    finger.set_angle(500, speed=300)
    calls = proto.write_shorts.call_args_list
    # Should write speed first, then angle
    assert call(1, 1528, [300]) in calls  # SPEED_SET + 3*2
    assert call(1, 1492, [500]) in calls  # ANGLE_SET + 3*2


def test_set_angle_with_force_limit():
    finger, proto = make_finger()
    finger.set_angle(500, force_limit=200)
    calls = proto.write_shorts.call_args_list
    assert call(1, 1504, [200]) in calls  # FORCE_SET + 3*2
    assert call(1, 1492, [500]) in calls  # ANGLE_SET + 3*2


def test_set_angle_delta():
    finger, proto = make_finger()
    # Current angle is 500
    proto.read_shorts.return_value = [500]
    finger.set_angle(-100, delta=True)
    # Should read current angle, then write 500 + (-100) = 400
    proto.read_shorts.assert_called_with(1, 1552, 1)  # ANGLE_ACT + 3*2
    proto.write_shorts.assert_called_with(1, 1492, [400])


def test_set_angle_delta_clamps_to_range():
    finger, proto = make_finger()
    proto.read_shorts.return_value = [50]
    finger.set_angle(-100, delta=True)
    # 50 + (-100) = -50, clamp to 0
    proto.write_shorts.assert_called_with(1, 1492, [0])


def test_set_angle_delta_not_supported_for_thumb_rotation():
    finger, proto = make_finger(dof_index=5, name="thumb_rotation")
    try:
        finger.set_angle(100, delta=True)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "delta" in str(e).lower()


def test_set_position():
    finger, proto = make_finger()
    finger._set_position(1000)
    proto.write_shorts.assert_called_with(1, 1480, [1000])  # POS_SET + 3*2


def test_read_angle():
    finger, proto = make_finger()
    proto.read_shorts.return_value = [750]
    assert finger.angle == 750
    proto.read_shorts.assert_called_with(1, 1552, 1)  # ANGLE_ACT + 3*2


def test_read_position():
    finger, proto = make_finger()
    proto.read_shorts.return_value = [1500]
    assert finger.position == 1500
    proto.read_shorts.assert_called_with(1, 1540, 1)  # POS_ACT + 3*2


def test_read_force():
    finger, proto = make_finger()
    proto.read_shorts.return_value = [300]
    assert finger.force == 300
    proto.read_shorts.assert_called_with(1, 1588, 1)  # FORCE_ACT + 3*2


def test_read_current():
    finger, proto = make_finger()
    proto.read_shorts.return_value = [450]
    assert finger.current == 450
    proto.read_shorts.assert_called_with(1, 1600, 1)  # CURRENT + 3*2


def test_read_temperature():
    finger, proto = make_finger()
    proto.read_bytes.return_value = [42]
    assert finger.temperature == 42
    proto.read_bytes.assert_called_with(1, 1621, 1)  # TEMP + 3


def test_read_status():
    finger, proto = make_finger()
    proto.read_bytes.return_value = [2]
    assert finger.status == Status.TARGET_REACHED
    proto.read_bytes.assert_called_with(1, 1615, 1)  # STATUS + 3


def test_read_error():
    finger, proto = make_finger()
    proto.read_bytes.return_value = [0x06]
    error = finger.error
    assert error["locked_rotor"] is False
    assert error["over_temp"] is True
    assert error["over_current"] is True
    assert error["abnormal_operation"] is False
    assert error["communication"] is False


def test_joint_limits():
    finger, proto = make_finger(dof_index=3, name="index")
    assert finger.joint_limits == JOINT_LIMITS["index"]


def test_set_default_speed():
    finger, proto = make_finger()
    finger.set_default_speed(500)
    proto.write_shorts.assert_called_with(1, 1038, [500])  # DEFAULT_SPEED_SET + 3*2


def test_set_default_force_limit():
    finger, proto = make_finger()
    finger.set_default_force_limit(300)
    proto.write_shorts.assert_called_with(1, 1050, [300])  # DEFAULT_FORCE_SET + 3*2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/kefhuang/Development/inspirepy && pytest tests/test_finger.py -v`
Expected: FAIL — cannot import `Finger`

- [ ] **Step 3: Implement finger.py**

```python
# inspirepy/finger.py
from inspirepy.constants import Status, ErrorFlag, JOINT_LIMITS
from inspirepy.registers import REGISTERS


class Finger:
    def __init__(self, protocol, hand_id: int, dof_index: int, name: str):
        self._protocol = protocol
        self._hand_id = hand_id
        self._dof_index = dof_index
        self._name = name

    def _short_addr(self, register_name: str) -> int:
        return REGISTERS[register_name].address + self._dof_index * 2

    def _byte_addr(self, register_name: str) -> int:
        return REGISTERS[register_name].address + self._dof_index

    def set_angle(self, value: int, *, delta: bool = False,
                  speed: int | None = None, force_limit: int | None = None):
        if delta:
            if self._name == "thumb_rotation":
                raise ValueError("delta mode is not supported for thumb_rotation (DOF 5)")
            current = self._protocol.read_shorts(self._hand_id, self._short_addr("ANGLE_ACT"), 1)[0]
            value = max(0, min(1000, current + value))

        if speed is not None:
            self._protocol.write_shorts(self._hand_id, self._short_addr("SPEED_SET"), [speed])
        if force_limit is not None:
            self._protocol.write_shorts(self._hand_id, self._short_addr("FORCE_SET"), [force_limit])

        self._protocol.write_shorts(self._hand_id, self._short_addr("ANGLE_SET"), [value])

    def _set_position(self, value: int):
        self._protocol.write_shorts(self._hand_id, self._short_addr("POS_SET"), [value])

    def set_default_speed(self, value: int):
        self._protocol.write_shorts(self._hand_id, self._short_addr("DEFAULT_SPEED_SET"), [value])

    def set_default_force_limit(self, value: int):
        self._protocol.write_shorts(self._hand_id, self._short_addr("DEFAULT_FORCE_SET"), [value])

    @property
    def angle(self) -> int:
        return self._protocol.read_shorts(self._hand_id, self._short_addr("ANGLE_ACT"), 1)[0]

    @property
    def position(self) -> int:
        return self._protocol.read_shorts(self._hand_id, self._short_addr("POS_ACT"), 1)[0]

    @property
    def force(self) -> int:
        return self._protocol.read_shorts(self._hand_id, self._short_addr("FORCE_ACT"), 1)[0]

    @property
    def current(self) -> int:
        return self._protocol.read_shorts(self._hand_id, self._short_addr("CURRENT"), 1)[0]

    @property
    def temperature(self) -> int:
        return self._protocol.read_bytes(self._hand_id, self._byte_addr("TEMP"), 1)[0]

    @property
    def status(self) -> Status:
        raw = self._protocol.read_bytes(self._hand_id, self._byte_addr("STATUS"), 1)[0]
        return Status(raw)

    @property
    def error(self) -> dict:
        raw = self._protocol.read_bytes(self._hand_id, self._byte_addr("ERROR"), 1)[0]
        return {
            "locked_rotor": bool(raw & ErrorFlag.LOCKED_ROTOR),
            "over_temp": bool(raw & ErrorFlag.OVER_TEMP),
            "over_current": bool(raw & ErrorFlag.OVER_CURRENT),
            "abnormal_operation": bool(raw & ErrorFlag.ABNORMAL_OPERATION),
            "communication": bool(raw & ErrorFlag.COMMUNICATION),
        }

    @property
    def joint_limits(self) -> dict:
        return JOINT_LIMITS[self._name]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/kefhuang/Development/inspirepy && pytest tests/test_finger.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add inspirepy/finger.py tests/test_finger.py
git commit -m "feat: add Finger class with per-finger control and sensors"
```

---

### Task 6: InspireHand class

**Files:**
- Create: `inspirepy/hand.py`
- Create: `tests/test_hand.py`

- [ ] **Step 1: Write tests for InspireHand**

```python
# tests/test_hand.py
import struct
from unittest.mock import MagicMock, patch, call
from inspirepy.hand import InspireHand
from inspirepy.constants import FINGER_NAMES, JOINT_LIMITS


@patch("inspirepy.hand.serial.Serial")
@patch("inspirepy.hand.Protocol")
def make_hand(MockProtocol, MockSerial):
    proto_instance = MockProtocol.return_value
    serial_instance = MockSerial.return_value
    # factory_reset writes to RESET_PARA
    hand = InspireHand("/dev/ttyUSB0")
    proto_instance.write_byte.assert_called_with(1, 1006, 1)
    return hand, proto_instance


def test_init_factory_resets():
    hand, proto = make_hand()
    proto.write_byte.assert_called_with(1, 1006, 1)


def test_finger_attributes_exist():
    hand, proto = make_hand()
    assert hand.little._dof_index == 0
    assert hand.ring._dof_index == 1
    assert hand.middle._dof_index == 2
    assert hand.index._dof_index == 3
    assert hand.thumb_bend._dof_index == 4
    assert hand.thumb_rotation._dof_index == 5


def test_set_angles_bulk():
    hand, proto = make_hand()
    hand.set_angles([100, 200, 300, 400, 500, 600])
    proto.write_shorts.assert_any_call(1, 1486, [100, 200, 300, 400, 500, 600])


def test_set_angles_with_speed_single():
    hand, proto = make_hand()
    hand.set_angles([500, 500, 500, 500, 500, 500], speed=300)
    proto.write_shorts.assert_any_call(1, 1522, [300, 300, 300, 300, 300, 300])


def test_set_angles_with_speed_list():
    hand, proto = make_hand()
    speeds = [100, 200, 300, 400, 500, 600]
    hand.set_angles([500, 500, 500, 500, 500, 500], speed=speeds)
    proto.write_shorts.assert_any_call(1, 1522, speeds)


def test_set_angles_with_force_limit_single():
    hand, proto = make_hand()
    hand.set_angles([500, 500, 500, 500, 500, 500], force_limit=200)
    proto.write_shorts.assert_any_call(1, 1498, [200, 200, 200, 200, 200, 200])


def test_set_angles_delta():
    hand, proto = make_hand()
    proto.read_shorts.return_value = [500, 500, 500, 500, 500, 500]
    hand.set_angles([-100, -100, -100, -100, -100, -100], delta=True)
    proto.read_shorts.assert_called_with(1, 1546, 6)
    proto.write_shorts.assert_any_call(1, 1486, [400, 400, 400, 400, 400, 400])


def test_get_angles():
    hand, proto = make_hand()
    proto.read_shorts.return_value = [100, 200, 300, 400, 500, 600]
    result = hand.get_angles()
    proto.read_shorts.assert_called_with(1, 1546, 6)
    assert result == [100, 200, 300, 400, 500, 600]


def test_get_forces():
    hand, proto = make_hand()
    proto.read_shorts.return_value = [10, 20, 30, 40, 50, 60]
    result = hand.get_forces()
    proto.read_shorts.assert_called_with(1, 1582, 6)
    assert result == [10, 20, 30, 40, 50, 60]


def test_get_currents():
    hand, proto = make_hand()
    proto.read_shorts.return_value = [100, 200, 300, 400, 500, 600]
    result = hand.get_currents()
    proto.read_shorts.assert_called_with(1, 1594, 6)
    assert result == [100, 200, 300, 400, 500, 600]


def test_get_temperatures():
    hand, proto = make_hand()
    proto.read_bytes.return_value = [30, 31, 32, 33, 34, 35]
    result = hand.get_temperatures()
    proto.read_bytes.assert_called_with(1, 1618, 6)
    assert result == [30, 31, 32, 33, 34, 35]


def test_get_statuses():
    hand, proto = make_hand()
    proto.read_bytes.return_value = [0, 1, 2, 3, 5, 6]
    result = hand.get_statuses()
    proto.read_bytes.assert_called_with(1, 1612, 6)
    assert len(result) == 6


def test_get_errors():
    hand, proto = make_hand()
    proto.read_bytes.return_value = [0, 0, 0x06, 0, 0, 0]
    result = hand.get_errors()
    proto.read_bytes.assert_called_with(1, 1606, 6)
    assert len(result) == 6


def test_voltage():
    hand, proto = make_hand()
    proto.read_shorts.return_value = [2400]
    assert hand.voltage == 2400
    proto.read_shorts.assert_called_with(1, 1472, 1)


def test_joint_limits():
    hand, proto = make_hand()
    limits = hand.joint_limits
    assert len(limits) == 6
    for name in FINGER_NAMES:
        assert name in limits
        assert limits[name] == JOINT_LIMITS[name]


def test_set_default_speeds_single():
    hand, proto = make_hand()
    hand.set_default_speeds(500)
    proto.write_shorts.assert_any_call(1, 1032, [500, 500, 500, 500, 500, 500])


def test_set_default_speeds_list():
    hand, proto = make_hand()
    speeds = [100, 200, 300, 400, 500, 600]
    hand.set_default_speeds(speeds)
    proto.write_shorts.assert_any_call(1, 1032, speeds)


def test_set_default_force_limits_single():
    hand, proto = make_hand()
    hand.set_default_force_limits(300)
    proto.write_shorts.assert_any_call(1, 1044, [300, 300, 300, 300, 300, 300])


def test_clear_errors():
    hand, proto = make_hand()
    hand.clear_errors()
    proto.write_byte.assert_called_with(1, 1004, 1)


def test_calibrate_force_sensors():
    hand, proto = make_hand()
    hand.calibrate_force_sensors()
    proto.write_byte.assert_called_with(1, 1009, 1)


def test_set_id():
    hand, proto = make_hand()
    hand.set_id(5)
    proto.write_byte.assert_called_with(1, 1000, 5)
    assert hand._hand_id == 5


def test_set_baudrate():
    hand, proto = make_hand()
    hand.set_baudrate(57600)
    proto.write_byte.assert_called_with(1, 1002, 1)  # BaudRate.B57600 == 1


def test_context_manager():
    with patch("inspirepy.hand.serial.Serial") as MockSerial, \
         patch("inspirepy.hand.Protocol"):
        with InspireHand("/dev/ttyUSB0") as hand:
            assert hand is not None
        MockSerial.return_value.close.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/kefhuang/Development/inspirepy && pytest tests/test_hand.py -v`
Expected: FAIL — cannot import `InspireHand` from `inspirepy.hand`

- [ ] **Step 3: Implement hand.py**

```python
# inspirepy/hand.py
import serial

from inspirepy.constants import (
    Status, ErrorFlag, FINGER_NAMES, JOINT_LIMITS, NUM_DOFS,
    BAUD_RATE_LOOKUP, BAUD_RATE_VALUES,
)
from inspirepy.registers import REGISTERS
from inspirepy.protocol import Protocol
from inspirepy.finger import Finger


class InspireHand:
    def __init__(self, port: str, baudrate: int = 115200, hand_id: int = 1):
        self._hand_id = hand_id
        self._serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            parity=serial.PARITY_NONE,
            timeout=1.0,
        )
        self._protocol = Protocol(self._serial)

        # Create finger objects
        self.little = Finger(self._protocol, self._hand_id, 0, "little")
        self.ring = Finger(self._protocol, self._hand_id, 1, "ring")
        self.middle = Finger(self._protocol, self._hand_id, 2, "middle")
        self.index = Finger(self._protocol, self._hand_id, 3, "index")
        self.thumb_bend = Finger(self._protocol, self._hand_id, 4, "thumb_bend")
        self.thumb_rotation = Finger(self._protocol, self._hand_id, 5, "thumb_rotation")

        self._fingers = [
            self.little, self.ring, self.middle,
            self.index, self.thumb_bend, self.thumb_rotation,
        ]

        # Factory reset for deterministic starting state
        self._protocol.write_byte(self._hand_id, REGISTERS["RESET_PARA"].address, 1)

    def close(self):
        self._serial.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    # -- Bulk control --

    def set_angles(self, angles: list[int], *, delta: bool = False,
                   speed: int | list[int] | None = None,
                   force_limit: int | list[int] | None = None):
        if len(angles) != NUM_DOFS:
            raise ValueError(f"Expected {NUM_DOFS} angles, got {len(angles)}")

        if speed is not None:
            if isinstance(speed, int):
                speed = [speed] * NUM_DOFS
            self._protocol.write_shorts(self._hand_id, REGISTERS["SPEED_SET"].address, speed)

        if force_limit is not None:
            if isinstance(force_limit, int):
                force_limit = [force_limit] * NUM_DOFS
            self._protocol.write_shorts(self._hand_id, REGISTERS["FORCE_SET"].address, force_limit)

        if delta:
            current = self._protocol.read_shorts(
                self._hand_id, REGISTERS["ANGLE_ACT"].address, NUM_DOFS
            )
            angles = [max(0, min(1000, c + d)) for c, d in zip(current, angles)]

        self._protocol.write_shorts(self._hand_id, REGISTERS["ANGLE_SET"].address, angles)

    def set_default_speeds(self, speeds: int | list[int]):
        if isinstance(speeds, int):
            speeds = [speeds] * NUM_DOFS
        self._protocol.write_shorts(
            self._hand_id, REGISTERS["DEFAULT_SPEED_SET"].address, speeds
        )

    def set_default_force_limits(self, limits: int | list[int]):
        if isinstance(limits, int):
            limits = [limits] * NUM_DOFS
        self._protocol.write_shorts(
            self._hand_id, REGISTERS["DEFAULT_FORCE_SET"].address, limits
        )

    # -- Bulk sensor reads --

    def get_angles(self) -> list[int]:
        return self._protocol.read_shorts(
            self._hand_id, REGISTERS["ANGLE_ACT"].address, NUM_DOFS
        )

    def get_forces(self) -> list[int]:
        return self._protocol.read_shorts(
            self._hand_id, REGISTERS["FORCE_ACT"].address, NUM_DOFS
        )

    def get_currents(self) -> list[int]:
        return self._protocol.read_shorts(
            self._hand_id, REGISTERS["CURRENT"].address, NUM_DOFS
        )

    def get_temperatures(self) -> list[int]:
        return self._protocol.read_bytes(
            self._hand_id, REGISTERS["TEMP"].address, NUM_DOFS
        )

    def get_statuses(self) -> list[Status]:
        raw = self._protocol.read_bytes(
            self._hand_id, REGISTERS["STATUS"].address, NUM_DOFS
        )
        return [Status(v) for v in raw]

    def get_errors(self) -> list[dict]:
        raw = self._protocol.read_bytes(
            self._hand_id, REGISTERS["ERROR"].address, NUM_DOFS
        )
        return [
            {
                "locked_rotor": bool(v & ErrorFlag.LOCKED_ROTOR),
                "over_temp": bool(v & ErrorFlag.OVER_TEMP),
                "over_current": bool(v & ErrorFlag.OVER_CURRENT),
                "abnormal_operation": bool(v & ErrorFlag.ABNORMAL_OPERATION),
                "communication": bool(v & ErrorFlag.COMMUNICATION),
            }
            for v in raw
        ]

    # -- System properties --

    @property
    def voltage(self) -> int:
        return self._protocol.read_shorts(
            self._hand_id, REGISTERS["VLTAGE"].address, 1
        )[0]

    @property
    def joint_limits(self) -> dict:
        return {name: JOINT_LIMITS[name] for name in FINGER_NAMES}

    # -- System commands --

    def clear_errors(self):
        self._protocol.write_byte(
            self._hand_id, REGISTERS["CLEAR_ERROR"].address, 1
        )

    def calibrate_force_sensors(self):
        self._protocol.write_byte(
            self._hand_id, REGISTERS["GESTURE_FORCE_CLB"].address, 1
        )

    def set_id(self, new_id: int):
        if not 1 <= new_id <= 254:
            raise ValueError(f"Hand ID must be 1-254, got {new_id}")
        self._protocol.write_byte(
            self._hand_id, REGISTERS["HAND_ID"].address, new_id
        )
        self._hand_id = new_id
        for finger in self._fingers:
            finger._hand_id = new_id

    def set_baudrate(self, baudrate: int):
        if baudrate not in BAUD_RATE_LOOKUP:
            raise ValueError(f"Baudrate must be one of {list(BAUD_RATE_LOOKUP.keys())}")
        code = BAUD_RATE_LOOKUP[baudrate]
        self._protocol.write_byte(
            self._hand_id, REGISTERS["REDU_RATIO"].address, code
        )
        self._serial.baudrate = baudrate
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/kefhuang/Development/inspirepy && pytest tests/test_hand.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add inspirepy/hand.py tests/test_hand.py
git commit -m "feat: add InspireHand class with bulk ops and system commands"
```

---

### Task 7: Config save/load

**Files:**
- Modify: `inspirepy/hand.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write tests for config**

```python
# tests/test_config.py
import os
import tempfile
import yaml
from unittest.mock import patch, MagicMock
from inspirepy.hand import InspireHand


@patch("inspirepy.hand.serial.Serial")
@patch("inspirepy.hand.Protocol")
def make_hand(MockProtocol, MockSerial):
    proto = MockProtocol.return_value
    hand = InspireHand("/dev/ttyUSB0")
    return hand, proto


def test_save_config(tmp_path):
    hand, proto = make_hand()
    # Mock reading current config from hand
    proto.read_shorts.side_effect = [
        [500, 500, 500, 500, 500, 500],   # DEFAULT_SPEED_SET
        [300, 300, 300, 300, 300, 300],   # DEFAULT_FORCE_SET
        [1500, 1500, 1500, 1500, 1500, 1500],  # CURRENT_LIMIT
    ]
    proto.read_bytes.side_effect = [
        [1],  # HAND_ID
        [0],  # REDU_RATIO
    ]

    path = tmp_path / "config.yaml"
    hand.save_config(str(path))

    with open(path) as f:
        config = yaml.safe_load(f)

    assert config["hand_id"] == 1
    assert config["baudrate"] == 115200
    assert config["default_speeds"]["little"] == 500
    assert config["default_force_limits"]["little"] == 300
    assert config["current_limits"]["little"] == 1500


def test_load_config(tmp_path):
    hand, proto = make_hand()

    config = {
        "hand_id": 2,
        "baudrate": 115200,
        "default_speeds": {
            "little": 400, "ring": 400, "middle": 400,
            "index": 400, "thumb_bend": 400, "thumb_rotation": 400,
        },
        "default_force_limits": {
            "little": 250, "ring": 250, "middle": 250,
            "index": 250, "thumb_bend": 250, "thumb_rotation": 250,
        },
        "current_limits": {
            "little": 1000, "ring": 1000, "middle": 1000,
            "index": 1000, "thumb_bend": 1000, "thumb_rotation": 1000,
        },
    }

    path = tmp_path / "config.yaml"
    with open(path, "w") as f:
        yaml.dump(config, f)

    hand.load_config(str(path))

    proto.write_byte.assert_any_call(1, 1000, 2)  # HAND_ID
    proto.write_shorts.assert_any_call(2, 1032, [400, 400, 400, 400, 400, 400])
    proto.write_shorts.assert_any_call(2, 1044, [250, 250, 250, 250, 250, 250])
    proto.write_shorts.assert_any_call(2, 1020, [1000, 1000, 1000, 1000, 1000, 1000])


def test_save_config_uses_finger_names(tmp_path):
    hand, proto = make_hand()
    proto.read_shorts.side_effect = [
        [100, 200, 300, 400, 500, 600],
        [100, 200, 300, 400, 500, 600],
        [100, 200, 300, 400, 500, 600],
    ]
    proto.read_bytes.side_effect = [
        [1],
        [0],
    ]

    path = tmp_path / "config.yaml"
    hand.save_config(str(path))

    with open(path) as f:
        config = yaml.safe_load(f)

    for section in ["default_speeds", "default_force_limits", "current_limits"]:
        assert "little" in config[section]
        assert "ring" in config[section]
        assert "middle" in config[section]
        assert "index" in config[section]
        assert "thumb_bend" in config[section]
        assert "thumb_rotation" in config[section]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/kefhuang/Development/inspirepy && pytest tests/test_config.py -v`
Expected: FAIL — `InspireHand` has no `save_config` or `load_config`

- [ ] **Step 3: Add config methods to hand.py**

Add these methods to the `InspireHand` class:

```python
    # -- Config save/load --

    def save_config(self, path: str):
        import yaml
        from inspirepy.constants import FINGER_NAMES, BAUD_RATE_VALUES

        speeds = self._protocol.read_shorts(
            self._hand_id, REGISTERS["DEFAULT_SPEED_SET"].address, NUM_DOFS
        )
        force_limits = self._protocol.read_shorts(
            self._hand_id, REGISTERS["DEFAULT_FORCE_SET"].address, NUM_DOFS
        )
        current_limits = self._protocol.read_shorts(
            self._hand_id, REGISTERS["CURRENT_LIMIT"].address, NUM_DOFS
        )
        hand_id = self._protocol.read_bytes(
            self._hand_id, REGISTERS["HAND_ID"].address, 1
        )[0]
        baud_code = self._protocol.read_bytes(
            self._hand_id, REGISTERS["REDU_RATIO"].address, 1
        )[0]

        def to_named_dict(values):
            return {name: val for name, val in zip(FINGER_NAMES, values)}

        config = {
            "hand_id": hand_id,
            "baudrate": BAUD_RATE_VALUES.get(baud_code, 115200),
            "default_speeds": to_named_dict(speeds),
            "default_force_limits": to_named_dict(force_limits),
            "current_limits": to_named_dict(current_limits),
        }

        with open(path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def load_config(self, path: str):
        import yaml
        from inspirepy.constants import FINGER_NAMES, BAUD_RATE_LOOKUP

        with open(path) as f:
            config = yaml.safe_load(f)

        def from_named_dict(d):
            return [d[name] for name in FINGER_NAMES]

        if "hand_id" in config:
            new_id = config["hand_id"]
            self._protocol.write_byte(self._hand_id, REGISTERS["HAND_ID"].address, new_id)
            self._hand_id = new_id
            for finger in self._fingers:
                finger._hand_id = new_id

        if "baudrate" in config:
            baudrate = config["baudrate"]
            if baudrate in BAUD_RATE_LOOKUP:
                self._protocol.write_byte(
                    self._hand_id, REGISTERS["REDU_RATIO"].address, BAUD_RATE_LOOKUP[baudrate]
                )
                self._serial.baudrate = baudrate

        if "default_speeds" in config:
            speeds = from_named_dict(config["default_speeds"])
            self._protocol.write_shorts(
                self._hand_id, REGISTERS["DEFAULT_SPEED_SET"].address, speeds
            )

        if "default_force_limits" in config:
            limits = from_named_dict(config["default_force_limits"])
            self._protocol.write_shorts(
                self._hand_id, REGISTERS["DEFAULT_FORCE_SET"].address, limits
            )

        if "current_limits" in config:
            limits = from_named_dict(config["current_limits"])
            self._protocol.write_shorts(
                self._hand_id, REGISTERS["CURRENT_LIMIT"].address, limits
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/kefhuang/Development/inspirepy && pytest tests/test_config.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add inspirepy/hand.py tests/test_config.py
git commit -m "feat: add YAML config save/load"
```

---

### Task 8: ActionSequence class

**Files:**
- Create: `inspirepy/sequence.py`
- Create: `tests/test_sequence.py`

- [ ] **Step 1: Write tests for ActionSequence**

```python
# tests/test_sequence.py
import yaml
from unittest.mock import MagicMock, call
from inspirepy.sequence import ActionSequence
from inspirepy.constants import FINGER_NAMES


def make_sequence(slot=0):
    proto = MagicMock()
    seq = ActionSequence(protocol=proto, hand_id=1, slot=slot)
    return seq, proto


def test_add_step():
    seq, proto = make_sequence()
    seq.add_step(
        angles=[0, 0, 0, 0, 0, 0],
        speed=500,
        force_limit=300,
        duration=500,
    )
    assert len(seq._steps) == 1
    step = seq._steps[0]
    assert step["angles"] == [0, 0, 0, 0, 0, 0]
    assert step["speed"] == 500
    assert step["force_limit"] == 300
    assert step["duration"] == 500


def test_add_step_max_8():
    seq, proto = make_sequence()
    for i in range(8):
        seq.add_step(angles=[0]*6, speed=500, force_limit=300, duration=100)
    try:
        seq.add_step(angles=[0]*6, speed=500, force_limit=300, duration=100)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "8" in str(e)


def test_upload():
    seq, proto = make_sequence(slot=0)
    seq.add_step(angles=[100, 200, 300, 400, 500, 600], speed=500, force_limit=300, duration=1000)
    seq.add_step(angles=[600, 500, 400, 300, 200, 100], speed=800, force_limit=200, duration=500)
    seq.upload()

    calls = proto.write_byte.call_args_list
    # Should set index first
    assert call(1, 2320, 0) in calls  # ACTION_SEQ_INDEX = slot 0
    # Should write step count
    assert call(1, 2002, 2) in calls  # ACTION_SEQ_STEPNUM = 2
    # Should write check codes
    assert call(1, 2000, 0x90) in calls  # CHECK_DATA1
    assert call(1, 2001, 0xEB) in calls  # CHECK_DATA2
    # Should save
    assert call(1, 2321, 1) in calls  # SAVE_ACTION_SEQ

    # Should write step data via write_shorts
    assert proto.write_shorts.call_count == 2  # 2 steps


def test_run():
    seq, proto = make_sequence(slot=3)
    seq.add_step(angles=[0]*6, speed=500, force_limit=300, duration=100)
    seq.upload()
    proto.write_byte.reset_mock()

    seq.run()
    calls = proto.write_byte.call_args_list
    assert call(1, 2320, 3) in calls   # set index to slot 3
    assert call(1, 2322, 1) in calls   # ACTION_SEQ_RUN


def test_save_yaml(tmp_path):
    seq, proto = make_sequence()
    seq.add_step(angles=[0, 0, 0, 0, 0, 0], speed=500, force_limit=300, duration=500)
    seq.add_step(angles=[1000, 1000, 1000, 1000, 1000, 500], speed=500, force_limit=300, duration=300)

    path = tmp_path / "wave.yaml"
    seq.save(str(path))

    with open(path) as f:
        data = yaml.safe_load(f)

    assert len(data["steps"]) == 2
    step0 = data["steps"][0]
    assert step0["angles"]["little"] == 0
    assert step0["speed"] == 500
    assert step0["force_limit"] == 300
    assert step0["duration"] == 500


def test_load_yaml(tmp_path):
    data = {
        "steps": [
            {
                "angles": {"little": 0, "ring": 0, "middle": 0, "index": 0, "thumb_bend": 0, "thumb_rotation": 0},
                "speed": 500,
                "force_limit": 300,
                "duration": 500,
            },
            {
                "angles": {"little": 1000, "ring": 1000, "middle": 1000, "index": 1000, "thumb_bend": 1000, "thumb_rotation": 500},
                "speed": 800,
                "force_limit": 200,
                "duration": 300,
            },
        ]
    }
    path = tmp_path / "wave.yaml"
    with open(path, "w") as f:
        yaml.dump(data, f)

    proto = MagicMock()
    seq = ActionSequence.load(str(path), protocol=proto, hand_id=1, slot=0)
    assert len(seq._steps) == 2
    assert seq._steps[0]["angles"] == [0, 0, 0, 0, 0, 0]
    assert seq._steps[1]["angles"] == [1000, 1000, 1000, 1000, 1000, 500]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/kefhuang/Development/inspirepy && pytest tests/test_sequence.py -v`
Expected: FAIL — cannot import `ActionSequence`

- [ ] **Step 3: Implement sequence.py**

```python
# inspirepy/sequence.py
import yaml

from inspirepy.constants import FINGER_NAMES, NUM_DOFS
from inspirepy.registers import REGISTERS


class ActionSequence:
    MAX_STEPS = 8

    def __init__(self, protocol, hand_id: int, slot: int = 0):
        self._protocol = protocol
        self._hand_id = hand_id
        self._slot = slot
        self._steps = []

    def add_step(self, angles: list[int], speed: int, force_limit: int, duration: int):
        if len(self._steps) >= self.MAX_STEPS:
            raise ValueError(f"Maximum {self.MAX_STEPS} steps per sequence")
        if len(angles) != NUM_DOFS:
            raise ValueError(f"Expected {NUM_DOFS} angles, got {len(angles)}")
        self._steps.append({
            "angles": list(angles),
            "speed": speed,
            "force_limit": force_limit,
            "duration": duration,
        })

    def _encode_step(self, step: dict) -> list[int]:
        # Each step is 19 shorts:
        # 6 angles + 6 speeds + 6 force_limits + 1 duration = 19
        angles = step["angles"]
        speeds = [step["speed"]] * NUM_DOFS
        force_limits = [step["force_limit"]] * NUM_DOFS
        duration = step["duration"]
        return angles + speeds + force_limits + [duration]

    def upload(self):
        # 1. Set sequence index
        self._protocol.write_byte(
            self._hand_id, REGISTERS["ACTION_SEQ_INDEX"].address, self._slot
        )

        # 2. Write step data
        for i, step in enumerate(self._steps):
            step_data = self._encode_step(step)
            self._protocol.write_shorts(
                self._hand_id, REGISTERS[f"ACTION_SEQ_STEP_{i}"].address, step_data
            )

        # 3. Write step count
        self._protocol.write_byte(
            self._hand_id, REGISTERS["ACTION_SEQ_STEPNUM"].address, len(self._steps)
        )

        # 4. Write check codes
        self._protocol.write_byte(
            self._hand_id, REGISTERS["ACTION_SEQ_CHECK_DATA1"].address, 0x90
        )
        self._protocol.write_byte(
            self._hand_id, REGISTERS["ACTION_SEQ_CHECK_DATA2"].address, 0xEB
        )

        # 5. Save
        self._protocol.write_byte(
            self._hand_id, REGISTERS["SAVE_ACTION_SEQ"].address, 1
        )

    def run(self):
        self._protocol.write_byte(
            self._hand_id, REGISTERS["ACTION_SEQ_INDEX"].address, self._slot
        )
        self._protocol.write_byte(
            self._hand_id, REGISTERS["ACTION_SEQ_RUN"].address, 1
        )

    def save(self, path: str):
        def to_named_dict(values):
            return {name: val for name, val in zip(FINGER_NAMES, values)}

        data = {
            "steps": [
                {
                    "angles": to_named_dict(step["angles"]),
                    "speed": step["speed"],
                    "force_limit": step["force_limit"],
                    "duration": step["duration"],
                }
                for step in self._steps
            ]
        }

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @classmethod
    def load(cls, path: str, protocol, hand_id: int, slot: int = 0) -> "ActionSequence":
        with open(path) as f:
            data = yaml.safe_load(f)

        seq = cls(protocol=protocol, hand_id=hand_id, slot=slot)
        for step_data in data["steps"]:
            angles_dict = step_data["angles"]
            angles = [angles_dict[name] for name in FINGER_NAMES]
            seq.add_step(
                angles=angles,
                speed=step_data["speed"],
                force_limit=step_data["force_limit"],
                duration=step_data["duration"],
            )
        return seq
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/kefhuang/Development/inspirepy && pytest tests/test_sequence.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add inspirepy/sequence.py tests/test_sequence.py
git commit -m "feat: add ActionSequence class with upload/run/save/load"
```

---

### Task 9: Wire sequences into InspireHand

**Files:**
- Modify: `inspirepy/hand.py`
- Modify: `tests/test_hand.py`

- [ ] **Step 1: Write tests for hand sequence methods**

Add to `tests/test_hand.py`:

```python
from inspirepy.sequence import ActionSequence


def test_create_sequence():
    hand, proto = make_hand()
    seq = hand.create_sequence(slot=0)
    assert isinstance(seq, ActionSequence)


def test_load_sequence(tmp_path):
    hand, proto = make_hand()
    data = {
        "steps": [
            {
                "angles": {"little": 0, "ring": 0, "middle": 0, "index": 0, "thumb_bend": 0, "thumb_rotation": 0},
                "speed": 500,
                "force_limit": 300,
                "duration": 500,
            },
        ]
    }
    import yaml
    path = tmp_path / "seq.yaml"
    with open(path, "w") as f:
        yaml.dump(data, f)

    seq = hand.load_sequence(str(path), slot=0)
    assert isinstance(seq, ActionSequence)
    assert len(seq._steps) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/kefhuang/Development/inspirepy && pytest tests/test_hand.py::test_create_sequence tests/test_hand.py::test_load_sequence -v`
Expected: FAIL — `InspireHand` has no `create_sequence` or `load_sequence`

- [ ] **Step 3: Add sequence methods to hand.py**

Add to `InspireHand` class and add import at top of `hand.py`:

```python
from inspirepy.sequence import ActionSequence
```

Methods:

```python
    def create_sequence(self, slot: int = 0) -> ActionSequence:
        return ActionSequence(protocol=self._protocol, hand_id=self._hand_id, slot=slot)

    def load_sequence(self, path: str, slot: int = 0) -> ActionSequence:
        return ActionSequence.load(path, protocol=self._protocol, hand_id=self._hand_id, slot=slot)
```

- [ ] **Step 4: Run all tests to verify everything passes**

Run: `cd /home/kefhuang/Development/inspirepy && pytest -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add inspirepy/hand.py tests/test_hand.py
git commit -m "feat: wire ActionSequence into InspireHand"
```

---

### Task 10: Update __init__.py exports and final verification

**Files:**
- Modify: `inspirepy/__init__.py`

- [ ] **Step 1: Update __init__.py with full public exports**

```python
# inspirepy/__init__.py
from inspirepy.hand import InspireHand
from inspirepy.sequence import ActionSequence
from inspirepy.constants import Status, ErrorFlag, BaudRate

__all__ = ["InspireHand", "ActionSequence", "Status", "ErrorFlag", "BaudRate"]
```

- [ ] **Step 2: Run full test suite**

Run: `cd /home/kefhuang/Development/inspirepy && pytest -v`
Expected: All tests PASS

- [ ] **Step 3: Verify package imports work**

Run: `cd /home/kefhuang/Development/inspirepy && python -c "from inspirepy import InspireHand, ActionSequence, Status, ErrorFlag, BaudRate; print('All imports OK')"`
Expected: `All imports OK`

- [ ] **Step 4: Commit**

```bash
git add inspirepy/__init__.py
git commit -m "feat: finalize public API exports"
```
