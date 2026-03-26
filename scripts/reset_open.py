#!/usr/bin/env python3
"""Reset the hand to fully open pose.

Usage: python scripts/reset_open.py [port]
"""

import sys
from inspirepy import InspireHand

port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

hand = InspireHand(port)
hand.set_angles([1000, 1000, 1000, 1000, 1000, 1000], speed=500)
print("Open pose set.")
hand.close()
