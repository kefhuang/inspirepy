#!/usr/bin/env python3
"""Reset the hand to a fist pose.

Moves thumb into position first, then closes four fingers.

Usage: python scripts/reset_fist.py [port]
"""

import sys
import time
from inspirepy import InspireHand

port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

hand = InspireHand(port)

# Thumb into position first
hand.thumb_bend.set_angle(148, speed=500)
hand.thumb_rotation.set_angle(894, speed=500)
time.sleep(1)

# Then close four fingers
hand.little.set_angle(0, speed=500)
hand.ring.set_angle(0, speed=500)
hand.middle.set_angle(0, speed=500)
hand.index.set_angle(0, speed=500)
time.sleep(1)

print("Fist pose set.")
hand.close()
