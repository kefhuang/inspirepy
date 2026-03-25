from enum import Enum, IntEnum


NUM_DOFS = 6

FINGER_NAMES = [
    "little", "ring", "middle", "index", "thumb_bend", "thumb_rotation"
]


class Status(IntEnum):
    UNCLENCHING = 0
    GRASPING = 1
    TARGET_REACHED = 2
    FORCE_LIMIT_REACHED = 3
    CURRENT_PROTECTION = 5
    LOCKED_ROTOR = 6
    ACTUATOR_FAULT = 7


class ErrorFlag(IntEnum):
    LOCKED_ROTOR = 0x01
    OVER_TEMP = 0x02
    OVER_CURRENT = 0x04
    ABNORMAL_OPERATION = 0x08
    COMMUNICATION = 0x10


class BaudRate(IntEnum):
    B115200 = 0
    B57600 = 1
    B19200 = 2


class FingerName(str, Enum):
    LITTLE = "little"
    RING = "ring"
    MIDDLE = "middle"
    INDEX = "index"
    THUMB_BEND = "thumb_bend"
    THUMB_ROTATION = "thumb_rotation"


BAUD_RATE_VALUES = {
    BaudRate.B115200: 115200,
    BaudRate.B57600: 57600,
    BaudRate.B19200: 19200,
}

BAUD_RATE_LOOKUP = {v: k for k, v in BAUD_RATE_VALUES.items()}


JOINT_LIMITS = {
    "little":         {"min_deg": 19.0,  "max_deg": 176.7, "angle_range": (0, 1000)},
    "ring":           {"min_deg": 19.0,  "max_deg": 176.7, "angle_range": (0, 1000)},
    "middle":         {"min_deg": 19.0,  "max_deg": 176.7, "angle_range": (0, 1000)},
    "index":          {"min_deg": 19.0,  "max_deg": 176.7, "angle_range": (0, 1000)},
    "thumb_bend":     {"min_deg": -13.0, "max_deg": 53.6,  "angle_range": (0, 1000)},
    "thumb_rotation": {"min_deg": 90.0,  "max_deg": 165.0, "angle_range": (0, 1000)},
}
