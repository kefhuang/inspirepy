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
