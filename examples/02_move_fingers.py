"""Move each finger individually, opening it back before moving the next.

Starts with the little finger and works inward. Each finger opens
before the next one closes to avoid collisions (especially the thumb).

Angle convention: 0 = fully closed, 1000 = fully open.
Fist pose: four fingers at 0, thumb_bend 148, thumb_rotation 894.
"""

import time
from inspirepy import InspireHand

hand = InspireHand("/dev/ttyUSB0")

OPEN = [1000, 1000, 1000, 1000, 1000, 1000]
FIST = [0, 0, 0, 0, 148, 894]

# Open hand
print("Opening hand...")
hand.set_angles(OPEN, speed=500)
time.sleep(1)

# Close and open each finger one at a time, starting from little
fingers = [
    ("little", hand.little),
    ("ring", hand.ring),
    ("middle", hand.middle),
    ("index", hand.index),
    ("thumb bend", hand.thumb_bend),
    ("thumb rotation", hand.thumb_rotation),
]

for name, finger in fingers:
    print(f"Closing {name}...")
    finger.set_angle(0, speed=500)
    time.sleep(0.8)
    print(f"  angle: {finger.angle}, force: {finger.force} g")

    print(f"Opening {name}...")
    finger.set_angle(1000, speed=500)
    time.sleep(0.8)

# Reset to fist pose: thumb first, then four fingers
print("\nResetting to fist pose...")
hand.set_angles(FIST, speed=500)
time.sleep(1)

hand.close()
print("Done.")
