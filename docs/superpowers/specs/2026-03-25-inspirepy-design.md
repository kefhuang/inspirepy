# inspirepy — Python Library for Inspire-Robots RH56 Dexterous Hand

## Overview

A Python library for controlling the Inspire-Robots RH56 Series Dexterous Hand over USB serial. Wraps the full register map from the manufacturer's documentation into an intuitive, object-oriented API with named finger access.

## Dependencies

- `pyserial` — serial communication
- `pyyaml` — config and sequence file I/O

## Package Structure

```
inspirepy/
├── __init__.py          # exports InspireHand
├── hand.py              # InspireHand class (connection, bulk ops, system commands)
├── finger.py            # Finger class (per-finger control and sensors)
├── protocol.py          # low-level packet build/parse (0xEB/0x90 framing, checksum)
├── registers.py         # register address map and metadata
├── sequence.py          # ActionSequence builder
└── constants.py         # enums for status codes, error flags, finger names, baud rates
```

## Communication

- **Protocol:** Custom Inspire serial protocol (0xEB/0x90 packet headers, simple checksum)
- **Transport:** RS485 over USB (the included USB cable has a built-in USB-to-RS485 converter)
- **Default baud rate:** 115200 (8 data bits, 1 stop bit, no parity)
- **Behavior on init:** Always sends a factory_reset command so the hand starts from a known state

## Connection

```python
from inspirepy import InspireHand

# Basic (defaults: baudrate=115200, hand_id=1)
hand = InspireHand("/dev/ttyUSB0")

# With options
hand = InspireHand("/dev/ttyUSB0", baudrate=115200, hand_id=1)

# Context manager
with InspireHand("/dev/ttyUSB0") as hand:
    ...

# Cleanup
hand.close()
```

The constructor automatically calls factory_reset on the hand to ensure a deterministic starting state.

## Finger Objects

Six named finger attributes on the hand, one per DOF:

| Attribute          | DOF | Description      |
|--------------------|-----|------------------|
| `hand.little`      | 0   | Little finger    |
| `hand.ring`        | 1   | Ring finger      |
| `hand.middle`      | 2   | Middle finger    |
| `hand.index`       | 3   | Index finger     |
| `hand.thumb_bend`  | 4   | Thumb bending    |
| `hand.thumb_rotation` | 5 | Thumb rotation   |

All six finger objects have an identical API — no special cases.

### Per-Finger Control

```python
# Absolute angle (0-1000, -1 = no action)
finger.set_angle(500)

# Delta angle (relative to current actual angle)
finger.set_angle(-100, delta=True)

# With speed and/or force_limit overrides
finger.set_angle(500, speed=300, force_limit=200)

# Raw actuator position (not recommended, use set_angle instead)
finger._set_position(1000)  # 0-2000, -1 = no action

# Set defaults (used when speed/force_limit not passed to set_angle)
finger.set_default_speed(500)
finger.set_default_force_limit(300)
```

When `speed` or `force_limit` are not passed to `set_angle`, the hand uses the currently configured defaults.

Note: `delta=True` is not supported for `thumb_rotation` (DOF 5) since it does not accept -1 (no action). For thumb rotation, `set_angle` always requires an absolute value (0-1000).

### Per-Finger Sensors and Properties (read-only)

```python
finger.angle          # actual angle (0-1000)
finger.position       # actual actuator position (0-2000)
finger.force          # actual force applied (0-1000, unit: g)
finger.current        # actuator current (0-1000, unit: mA)
finger.temperature    # actuator temperature (0-100, unit: °C)
finger.status         # Status enum (UNCLENCHING, GRASPING, TARGET_REACHED, FORCE_LIMIT_REACHED, CURRENT_PROTECTION, LOCKED_ROTOR, ACTUATOR_FAULT)
finger.error          # error flags (locked_rotor, over_temp, over_current, abnormal_operation, communication_error)
finger.joint_limits   # {"min_deg": 19.0, "max_deg": 176.7, "angle_range": (0, 1000)}
```

## Bulk Operations

Operate on all 6 DOFs at once. Order: little, ring, middle, index, thumb_bend, thumb_rotation.

### Bulk Control

```python
# Set all angles (list of 6)
hand.set_angles([500, 500, 500, 500, 500, 500])

# Delta mode
hand.set_angles([-100, -100, -100, -100, -100, -100], delta=True)

# With per-finger speed/force (list of 6)
hand.set_angles([500, 500, 500, 500, 500, 500],
                speed=[300, 300, 300, 500, 500, 500],
                force_limit=[200, 200, 200, 400, 400, 400])

# Single value = applied to all 6
hand.set_angles([500, 500, 500, 500, 500, 500], speed=300, force_limit=200)

# Bulk defaults — single value or list of 6
hand.set_default_speeds(500)
hand.set_default_speeds([500, 500, 500, 300, 300, 300])
hand.set_default_force_limits(200)
hand.set_default_force_limits([200, 200, 200, 400, 400, 400])
```

### Bulk Sensor Reads

All return a list of 6 values in DOF order.

```python
hand.get_angles()
hand.get_forces()
hand.get_currents()
hand.get_temperatures()
hand.get_statuses()
hand.get_errors()
```

### System Properties

```python
hand.voltage       # system voltage (read-only)
hand.joint_limits  # all 6 fingers' limits as a dict keyed by finger name
```

## System Commands

```python
# Calibrate force sensors (hand must be unloaded, takes ~6 seconds)
hand.calibrate_force_sensors()

# Clear clearable errors (locked-rotor, over-current, abnormal operation, communication)
# Over-temperature errors clear automatically when temperature drops
hand.clear_errors()

# Change hand ID (1-254, for multi-hand bus setups)
hand.set_id(2)

# Change baud rate (115200, 57600, or 19200)
hand.set_baudrate(115200)
```

## Configuration Save/Load

Settings are managed on the computer side via YAML files. The hand always factory resets on init.

```python
hand.save_config("my_config.yaml")
hand.load_config("my_config.yaml")
```

Config file format:

```yaml
hand_id: 1
baudrate: 115200

default_speeds:
  little: 500
  ring: 500
  middle: 500
  index: 500
  thumb_bend: 500
  thumb_rotation: 500

default_force_limits:
  little: 300
  ring: 300
  middle: 300
  index: 300
  thumb_bend: 300
  thumb_rotation: 300

current_limits:
  little: 1500
  ring: 1500
  middle: 1500
  index: 1500
  thumb_bend: 1500
  thumb_rotation: 1500
```

## Action Sequences

Programmable multi-step gesture sequences. Max 8 steps per sequence, 40 sequences storable on the hand.

### Creating and Running

```python
seq = hand.create_sequence()

seq.add_step(
    angles=[0, 0, 0, 0, 0, 0],
    speed=500,
    force_limit=300,
    duration=500          # hold for 500ms
)
seq.add_step(
    angles=[1000, 1000, 1000, 1000, 1000, 500],
    speed=500,
    force_limit=300,
    duration=300
)

seq.upload()
seq.run()
```

### Stopping a Sequence

Any direct control command interrupts a running sequence:

```python
hand.set_angles([0, 0, 0, 0, 0, 0])  # overrides running sequence
```

### Save/Load Sequences

```python
seq.save("wave.yaml")
seq = hand.load_sequence("wave.yaml")
```

Sequence YAML format:

```yaml
steps:
  - angles:
      little: 0
      ring: 0
      middle: 0
      index: 0
      thumb_bend: 0
      thumb_rotation: 0
    speed: 500
    force_limit: 300
    duration: 500

  - angles:
      little: 1000
      ring: 1000
      middle: 1000
      index: 1000
      thumb_bend: 1000
      thumb_rotation: 500
    speed: 500
    force_limit: 300
    duration: 300
```

## Protocol Layer (internal)

The protocol module handles the low-level Inspire serial protocol:

- **Packet header:** 0xEB 0x90 (request), 0x90 0xEB (response)
- **Read register:** flag 0x11, sends address + length, receives data
- **Write register:** flag 0x12, sends address + data, receives acknowledgment
- **Checksum:** low-order byte of the sum of all bytes after the header
- **Data format:** 16-bit signed shorts in little-endian byte order for multi-byte register groups

### Action Sequence Protocol

Writing an action sequence to the hand requires these steps in order:

1. Set `ACTION_SEQ_INDEX` to the desired sequence slot (0-39)
2. Write step data to `ACTION_SEQ_STEP(0)` through `ACTION_SEQ_STEP(7)`
3. Write total step count to `ACTION_SEQ_STEPNUM`
4. Write check codes: `ACTION_SEQ_CHECK_DATA1 = 0x90`, `ACTION_SEQ_CHECK_DATA2 = 0xEB`
5. Write 1 to `SAVE_ACTION_SEQ` to persist
6. Write 1 to `ACTION_SEQ_RUN` to execute

Reading a stored sequence:

1. Set `ACTION_SEQ_INDEX` to the desired sequence slot
2. Read `ACTION_SEQ_CHECK_DATA1` and `ACTION_SEQ_CHECK_DATA2` — if they equal 0x90 and 0xEB respectively, the sequence is valid
3. Read `ACTION_SEQ_STEPNUM` for the step count
4. Read step data from `ACTION_SEQ_STEP(0)` through `ACTION_SEQ_STEP(n-1)`

## Physical Angle Ranges

The abstract angle values (0-1000) map to physical degrees:

| DOF | Finger | Physical Range |
|-----|--------|---------------|
| 0-3 | Little, Ring, Middle, Index | 19° to 176.7° |
| 4   | Thumb bending | -13° to 53.6° |
| 5   | Thumb rotation | 90° to 165° |

## Register Map (internal)

Complete register address map derived from the manufacturer documentation:

| Address | Name                | Type          | R/W | Description                              |
|---------|---------------------|---------------|-----|------------------------------------------|
| 1000    | HAND_ID             | 1 byte        | W/R | Device ID (1-254)                        |
| 1002    | REDU_RATIO          | 1 byte        | W/R | Baud rate (0=115200, 1=57600, 2=19200)   |
| 1004    | CLEAR_ERROR         | 1 byte        | W/R | Write 1 to clear errors                  |
| 1005    | SAVE                | 1 byte        | W/R | Write 1 to save to flash                 |
| 1006    | RESET_PARA          | 1 byte        | W/R | Write 1 to factory reset                 |
| 1009    | GESTURE_FORCE_CLB   | 1 byte        | W/R | Write 1 to calibrate force sensors       |
| 1020    | CURRENT_LIMIT(m)    | 6 short       | W/R | Current protection per DOF (mA, 0-1500)  |
| 1032    | DEFAULT_SPEED_SET(m)| 6 short       | W/R | Power-on speed per DOF (0-1000)          |
| 1044    | DEFAULT_FORCE_SET(m)| 6 short       | W/R | Power-on force threshold per DOF (g, 0-1000; DOF 4 thumb_bend: 0-1500) |
| 1472    | VLTAGE              | 1 short       | R   | System voltage                           |
| 1474    | POS_SET(m)          | 6 short       | W/R | Target actuator position per DOF (0-2000, -1 = no action). Exposed as `_set_position` (not recommended). |
| 1486    | ANGLE_SET(m)        | 6 short       | W/R | Target angle per DOF (-1, 0-1000; DOF 5 thumb_rotation: 0-1000 only, no -1) |
| 1498    | FORCE_SET(m)        | 6 short       | W/R | Force control threshold per DOF (g, 0-1000) |
| 1522    | SPEED_SET(m)        | 6 short       | W/R | Speed per DOF (0-1000)                   |
| 1534    | POS_ACT(m)          | 6 short       | R   | Actual actuator position per DOF (0-2000)|
| 1546    | ANGLE_ACT(m)        | 6 short       | R   | Actual angle per DOF (0-1000)            |
| 1582    | FORCE_ACT(m)        | 6 short       | R   | Actual force per DOF (g, 0-1000)         |
| 1594    | CURRENT(m)          | 6 short       | R   | Actuator current per DOF (mA, 0-1000)    |
| 1606    | ERROR(m)            | 6 byte        | R   | Error codes per DOF (bitmask)            |
| 1612    | STATUS(m)           | 6 byte        | R   | Status per DOF                           |
| 1618    | TEMP(m)             | 6 byte        | R   | Temperature per DOF (°C, 0-100)          |
| 2000    | ACTION_SEQ_CHECK_DATA1 | 1 byte     | W/R | Action sequence check code 1 (valid = 0x90) |
| 2001    | ACTION_SEQ_CHECK_DATA2 | 1 byte     | W/R | Action sequence check code 2 (valid = 0xEB) |
| 2002    | ACTION_SEQ_STEPNUM  | 1 byte        | W/R | Total steps in current sequence          |
| 2016    | ACTION_SEQ_STEP(0)  | 19 short      | W/R | Sequence step 0 data                     |
| 2054    | ACTION_SEQ_STEP(1)  | 19 short      | W/R | Sequence step 1 data                     |
| 2092    | ACTION_SEQ_STEP(2)  | 19 short      | W/R | Sequence step 2 data                     |
| 2130    | ACTION_SEQ_STEP(3)  | 19 short      | W/R | Sequence step 3 data                     |
| 2168    | ACTION_SEQ_STEP(4)  | 19 short      | W/R | Sequence step 4 data                     |
| 2206    | ACTION_SEQ_STEP(5)  | 19 short      | W/R | Sequence step 5 data                     |
| 2244    | ACTION_SEQ_STEP(6)  | 19 short      | W/R | Sequence step 6 data                     |
| 2282    | ACTION_SEQ_STEP(7)  | 19 short      | W/R | Sequence step 7 data                     |
| 2320    | ACTION_SEQ_INDEX    | 1 byte        | W/R | Action sequence index number             |
| 2321    | SAVE_ACTION_SEQ     | 1 byte        | W/R | Save current action sequence             |
| 2322    | ACTION_SEQ_RUN      | 1 byte        | W/R | Run current action sequence              |
| 2324    | ACTION_ADJUST_FORCE_SET | 2 byte    | W/R | Force control adjustment for sequences   |

## Error Codes (bitmask per DOF)

| Bit | Description               |
|-----|---------------------------|
| 0   | Locked-rotor error        |
| 1   | Over temperature error    |
| 2   | Over-current error        |
| 3   | Abnormal motor operation  |
| 4   | Communication error       |

## Status Codes (per DOF)

| Code | Description                              |
|------|------------------------------------------|
| 0    | Unclenching                              |
| 1    | Grasping                                 |
| 2    | Stopped — reached target position        |
| 3    | Stopped — reached force control value    |
| 5    | Stopped — current protection             |
| 6    | Stopped — locked-rotor                   |
| 7    | Stopped — actuator fault                 |

## Testing Strategy

- Unit tests for protocol layer (packet construction, parsing, checksum) using mock serial
- Unit tests for register map (correct addresses, lengths, types)
- Unit tests for config/sequence YAML serialization/deserialization
- Integration tests require physical hardware — document how to run them but don't include in default test suite
