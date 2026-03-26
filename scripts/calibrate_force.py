"""Calibrate the force sensors on the RH56 hand.

IMPORTANT: All fingers must be fully open and not touching anything
during calibration. The process takes about 6 seconds.
"""

import time
from inspirepy import InspireHand

FINGER_NAMES = ["little", "ring", "middle", "index", "thumb_bend", "thumb_rotation"]

hand = InspireHand("/dev/ttyUSB0")

# Read forces before calibration
forces_before = hand.get_forces()
print("Forces before calibration:")
for name, f in zip(FINGER_NAMES, forces_before):
    print(f"  {name:<16} {f:>5} g")

print()
print("Starting calibration...")
print("Make sure all fingers are open and not touching anything!")
time.sleep(2)

hand.calibrate_force_sensors()
print("Calibrating (6 seconds)...")
time.sleep(15)

# Flush serial buffer before reading
hand._serial.reset_input_buffer()

# Read forces after calibration
forces_after = hand.get_forces()
print()
print("Forces after calibration:")
for name, f in zip(FINGER_NAMES, forces_after):
    print(f"  {name:<16} {f:>5} g")

print()
print("Calibration complete.")
hand.close()
