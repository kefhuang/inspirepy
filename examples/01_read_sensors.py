"""Read all sensors from the RH56 hand."""

from inspirepy import InspireHand

hand = InspireHand("/dev/ttyUSB0")

# System voltage
print(f"Voltage: {hand.voltage}")

# Read all angles, forces, temperatures at once
print(f"Angles:       {hand.get_angles()}")
print(f"Forces:       {hand.get_forces()}")
print(f"Currents:     {hand.get_currents()}")
print(f"Temperatures: {hand.get_temperatures()}")
print(f"Statuses:     {hand.get_statuses()}")
print(f"Errors:       {hand.get_errors()}")

# Read individual finger sensors
print(f"\nIndex finger:")
print(f"  angle:       {hand.index.angle}")
print(f"  position:    {hand.index.position}")
print(f"  force:       {hand.index.force} g")
print(f"  current:     {hand.index.current} mA")
print(f"  temperature: {hand.index.temperature} °C")
print(f"  status:      {hand.index.status}")
print(f"  error:       {hand.index.error}")
print(f"  joint_limits: {hand.index.joint_limits}")

hand.close()
