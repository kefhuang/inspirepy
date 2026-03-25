"""Move each finger individually, then all together."""

import time
from inspirepy import InspireHand

hand = InspireHand("/dev/ttyUSB0")

# Open all fingers first
hand.set_angles([0, 0, 0, 0, 0, 0], speed=500)
time.sleep(1)

# Close each finger one at a time
fingers = [
    ("little",         hand.little),
    ("ring",           hand.ring),
    ("middle",         hand.middle),
    ("index",          hand.index),
    ("thumb bend",     hand.thumb_bend),
    ("thumb rotation", hand.thumb_rotation),
]

for name, finger in fingers:
    print(f"Closing {name}...")
    finger.set_angle(1000, speed=500)
    time.sleep(0.8)
    print(f"  angle: {finger.angle}, force: {finger.force} g")

    print(f"Opening {name}...")
    finger.set_angle(0, speed=500)
    time.sleep(0.8)

# Close all fingers at once
print("\nClosing all fingers...")
hand.set_angles([1000, 1000, 1000, 1000, 1000, 500], speed=300)
time.sleep(1)

# Open all fingers
print("Opening all fingers...")
hand.set_angles([0, 0, 0, 0, 0, 0], speed=300)
time.sleep(1)

hand.close()
print("Done.")
