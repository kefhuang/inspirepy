"""Read all sensors from the RH56 hand."""

from inspirepy import InspireHand, Status

FINGER_NAMES = ["little", "ring", "middle", "index", "thumb_bend", "thumb_rotation"]

hand = InspireHand("/dev/ttyUSB0")

print(f"System voltage: {hand.voltage}")
print()

angles = hand.get_angles()
forces = hand.get_forces()
currents = hand.get_currents()
temps = hand.get_temperatures()
statuses = hand.get_statuses()
errors = hand.get_errors()

# Header
print(f"{'Finger':<16} {'Angle':>6} {'Force':>7} {'Current':>8} {'Temp':>6} {'Status':<12} {'Errors'}")
print("-" * 80)

for i, name in enumerate(FINGER_NAMES):
    # Format status
    s = statuses[i]
    if isinstance(s, Status):
        status_str = s.name
    else:
        status_str = f"UNKNOWN({s})"

    # Format errors
    err = errors[i]
    active_errors = [k for k, v in err.items() if v]
    error_str = ", ".join(active_errors) if active_errors else "none"

    print(f"{name:<16} {angles[i]:>6} {forces[i]:>5} g {currents[i]:>5} mA {temps[i]:>3} C  {status_str:<12} {error_str}")

print()
print("Joint limits:")
for name, limits in hand.joint_limits.items():
    print(f"  {name:<16} {limits['min_deg']:>6.1f} to {limits['max_deg']:>5.1f} deg")

hand.close()
