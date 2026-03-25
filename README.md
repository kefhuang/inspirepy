# inspirepy

Python library for the Inspire-Robots RH56 Dexterous Hand.

## Install

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from inspirepy import InspireHand

hand = InspireHand("/dev/ttyUSB0")

# Read sensors
print(hand.get_angles())
print(hand.index.force)
print(hand.index.temperature)

# Move fingers
hand.set_angles([500, 500, 500, 500, 500, 500], speed=300)
hand.index.set_angle(0, speed=500, force_limit=200)

# Delta motion
hand.index.set_angle(-100, delta=True)

# Save/load config
hand.save_config("my_config.yaml")
hand.load_config("my_config.yaml")

hand.close()
```

## Linux USB Setup

The RH56 uses a CH340 USB-to-serial converter. On many Linux systems, you need to fix two issues before the device will work.

### 1. Remove brltty

`brltty` is a braille display service that misidentifies the CH340 chip and steals the serial port. The symptom is that `/dev/ttyUSB0` never appears even though the cable is plugged in.

Check if it's installed:

```bash
dpkg -l | grep brltty
```

If installed, remove it:

```bash
sudo systemctl stop brltty-udev
sudo systemctl disable brltty-udev
sudo apt remove -y brltty
```

Then unplug and replug the USB cable. Verify the device appears:

```bash
ls /dev/ttyUSB*
```

### 2. Set permissions

By default, `/dev/ttyUSB0` is only accessible by root. You'll get `PermissionError: [Errno 13] Permission denied` without fixing this.

Quick fix (resets on replug):

```bash
sudo chmod 666 /dev/ttyUSB0
```

Permanent fix (add your user to the `dialout` group):

```bash
sudo usermod -aG dialout $USER
```

Log out and back in for the group change to take effect.

## API

### Connection

```python
from inspirepy import InspireHand

# Basic
hand = InspireHand("/dev/ttyUSB0")

# With options
hand = InspireHand("/dev/ttyUSB0", baudrate=115200, hand_id=1)

# Context manager
with InspireHand("/dev/ttyUSB0") as hand:
    ...

# Factory reset on connect (optional, off by default)
hand = InspireHand("/dev/ttyUSB0", factory_reset=True)
```

### Per-Finger Control

Six fingers, each with the same API:

- `hand.little` (DOF 0)
- `hand.ring` (DOF 1)
- `hand.middle` (DOF 2)
- `hand.index` (DOF 3)
- `hand.thumb_bend` (DOF 4)
- `hand.thumb_rotation` (DOF 5)

```python
# Set angle (0=open, 1000=closed)
hand.index.set_angle(500)
hand.index.set_angle(500, speed=300, force_limit=200)
hand.index.set_angle(-100, delta=True)  # relative to current

# Read sensors
hand.index.angle          # actual angle
hand.index.force          # force in grams
hand.index.current        # current in mA
hand.index.temperature    # temperature in celsius
hand.index.status         # Status enum
hand.index.error          # error flags dict
hand.index.joint_limits   # physical angle range

# Set defaults
hand.index.set_default_speed(500)
hand.index.set_default_force_limit(300)
```

### Bulk Operations

```python
# All 6 DOFs: [little, ring, middle, index, thumb_bend, thumb_rotation]
hand.set_angles([500, 500, 500, 500, 500, 500])
hand.set_angles([500, 500, 500, 500, 500, 500], speed=300, force_limit=200)
hand.set_angles([-100, -100, -100, -100, -100, 300], delta=True)

# Read all
hand.get_angles()
hand.get_forces()
hand.get_currents()
hand.get_temperatures()
hand.get_statuses()
hand.get_errors()

# Defaults (single value or list of 6)
hand.set_default_speeds(500)
hand.set_default_force_limits([200, 200, 200, 200, 400, 200])
```

### System

```python
hand.voltage               # system voltage
hand.joint_limits           # all fingers' physical limits
hand.clear_errors()
hand.calibrate_force_sensors()  # ~6 seconds, hand must be unloaded
hand.set_id(2)              # for multi-hand bus setups
hand.set_baudrate(57600)    # 115200, 57600, or 19200
```

### Config Files

```python
hand.save_config("config.yaml")
hand.load_config("config.yaml")
```

### Action Sequences

```python
seq = hand.create_sequence(slot=0)
seq.add_step(angles=[0, 0, 0, 0, 0, 0], speed=500, force_limit=300, duration=500)
seq.add_step(angles=[1000, 1000, 1000, 1000, 1000, 500], speed=500, force_limit=300, duration=300)
seq.upload()
seq.run()

# Stop by sending any direct command
hand.set_angles([0, 0, 0, 0, 0, 0])

# Save/load sequences
seq.save("wave.yaml")
seq = hand.load_sequence("wave.yaml")
```

## Examples

See `examples/` for runnable scripts:

- `01_read_sensors.py` — read all sensor values
- `02_move_fingers.py` — move each finger individually, then all together
