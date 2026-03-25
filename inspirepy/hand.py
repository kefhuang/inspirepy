from typing import Optional, Union, List
import serial

from inspirepy.constants import (
    Status, ErrorFlag, FINGER_NAMES, JOINT_LIMITS, NUM_DOFS,
    BAUD_RATE_LOOKUP, BAUD_RATE_VALUES,
)
from inspirepy.registers import REGISTERS
from inspirepy.protocol import Protocol
from inspirepy.finger import Finger


class InspireHand:
    def __init__(self, port: str, baudrate: int = 115200, hand_id: int = 1):
        self._hand_id = hand_id
        self._serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            parity=serial.PARITY_NONE,
            timeout=1.0,
        )
        self._protocol = Protocol(self._serial)

        self.little = Finger(self._protocol, self._hand_id, 0, "little")
        self.ring = Finger(self._protocol, self._hand_id, 1, "ring")
        self.middle = Finger(self._protocol, self._hand_id, 2, "middle")
        self.index = Finger(self._protocol, self._hand_id, 3, "index")
        self.thumb_bend = Finger(self._protocol, self._hand_id, 4, "thumb_bend")
        self.thumb_rotation = Finger(self._protocol, self._hand_id, 5, "thumb_rotation")

        self._fingers = [
            self.little, self.ring, self.middle,
            self.index, self.thumb_bend, self.thumb_rotation,
        ]

        self._protocol.write_byte(self._hand_id, REGISTERS["RESET_PARA"].address, 1)

    def close(self):
        self._serial.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def set_angles(self, angles: List[int], *, delta: bool = False,
                   speed: Union[int, List[int], None] = None,
                   force_limit: Union[int, List[int], None] = None):
        if len(angles) != NUM_DOFS:
            raise ValueError(f"Expected {NUM_DOFS} angles, got {len(angles)}")

        if speed is not None:
            if isinstance(speed, int):
                speed = [speed] * NUM_DOFS
            self._protocol.write_shorts(self._hand_id, REGISTERS["SPEED_SET"].address, speed)

        if force_limit is not None:
            if isinstance(force_limit, int):
                force_limit = [force_limit] * NUM_DOFS
            self._protocol.write_shorts(self._hand_id, REGISTERS["FORCE_SET"].address, force_limit)

        if delta:
            current = self._protocol.read_shorts(
                self._hand_id, REGISTERS["ANGLE_ACT"].address, NUM_DOFS
            )
            angles = [max(0, min(1000, c + d)) for c, d in zip(current, angles)]

        self._protocol.write_shorts(self._hand_id, REGISTERS["ANGLE_SET"].address, angles)

    def set_default_speeds(self, speeds: Union[int, List[int]]):
        if isinstance(speeds, int):
            speeds = [speeds] * NUM_DOFS
        self._protocol.write_shorts(
            self._hand_id, REGISTERS["DEFAULT_SPEED_SET"].address, speeds
        )

    def set_default_force_limits(self, limits: Union[int, List[int]]):
        if isinstance(limits, int):
            limits = [limits] * NUM_DOFS
        self._protocol.write_shorts(
            self._hand_id, REGISTERS["DEFAULT_FORCE_SET"].address, limits
        )

    def get_angles(self) -> List[int]:
        return self._protocol.read_shorts(
            self._hand_id, REGISTERS["ANGLE_ACT"].address, NUM_DOFS
        )

    def get_forces(self) -> List[int]:
        return self._protocol.read_shorts(
            self._hand_id, REGISTERS["FORCE_ACT"].address, NUM_DOFS
        )

    def get_currents(self) -> List[int]:
        return self._protocol.read_shorts(
            self._hand_id, REGISTERS["CURRENT"].address, NUM_DOFS
        )

    def get_temperatures(self) -> List[int]:
        return self._protocol.read_bytes(
            self._hand_id, REGISTERS["TEMP"].address, NUM_DOFS
        )

    def get_statuses(self) -> list:
        raw = self._protocol.read_bytes(
            self._hand_id, REGISTERS["STATUS"].address, NUM_DOFS
        )
        return [Status(v) for v in raw]

    def get_errors(self) -> list:
        raw = self._protocol.read_bytes(
            self._hand_id, REGISTERS["ERROR"].address, NUM_DOFS
        )
        return [
            {
                "locked_rotor": bool(v & ErrorFlag.LOCKED_ROTOR),
                "over_temp": bool(v & ErrorFlag.OVER_TEMP),
                "over_current": bool(v & ErrorFlag.OVER_CURRENT),
                "abnormal_operation": bool(v & ErrorFlag.ABNORMAL_OPERATION),
                "communication": bool(v & ErrorFlag.COMMUNICATION),
            }
            for v in raw
        ]

    @property
    def voltage(self) -> int:
        return self._protocol.read_shorts(
            self._hand_id, REGISTERS["VLTAGE"].address, 1
        )[0]

    @property
    def joint_limits(self) -> dict:
        return {name: JOINT_LIMITS[name] for name in FINGER_NAMES}

    def clear_errors(self):
        self._protocol.write_byte(
            self._hand_id, REGISTERS["CLEAR_ERROR"].address, 1
        )

    def calibrate_force_sensors(self):
        self._protocol.write_byte(
            self._hand_id, REGISTERS["GESTURE_FORCE_CLB"].address, 1
        )

    def set_id(self, new_id: int):
        if not 1 <= new_id <= 254:
            raise ValueError(f"Hand ID must be 1-254, got {new_id}")
        self._protocol.write_byte(
            self._hand_id, REGISTERS["HAND_ID"].address, new_id
        )
        self._hand_id = new_id
        for finger in self._fingers:
            finger._hand_id = new_id

    def set_baudrate(self, baudrate: int):
        if baudrate not in BAUD_RATE_LOOKUP:
            raise ValueError(f"Baudrate must be one of {list(BAUD_RATE_LOOKUP.keys())}")
        code = BAUD_RATE_LOOKUP[baudrate]
        self._protocol.write_byte(
            self._hand_id, REGISTERS["REDU_RATIO"].address, code
        )
        self._serial.baudrate = baudrate

    def save_config(self, path: str):
        import yaml
        speeds = self._protocol.read_shorts(self._hand_id, REGISTERS["DEFAULT_SPEED_SET"].address, NUM_DOFS)
        force_limits = self._protocol.read_shorts(self._hand_id, REGISTERS["DEFAULT_FORCE_SET"].address, NUM_DOFS)
        current_limits = self._protocol.read_shorts(self._hand_id, REGISTERS["CURRENT_LIMIT"].address, NUM_DOFS)
        hand_id = self._protocol.read_bytes(self._hand_id, REGISTERS["HAND_ID"].address, 1)[0]
        baud_code = self._protocol.read_bytes(self._hand_id, REGISTERS["REDU_RATIO"].address, 1)[0]

        def to_named_dict(values):
            return {name: val for name, val in zip(FINGER_NAMES, values)}

        config = {
            "hand_id": hand_id,
            "baudrate": BAUD_RATE_VALUES.get(baud_code, 115200),
            "default_speeds": to_named_dict(speeds),
            "default_force_limits": to_named_dict(force_limits),
            "current_limits": to_named_dict(current_limits),
        }
        with open(path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def load_config(self, path: str):
        import yaml

        with open(path) as f:
            config = yaml.safe_load(f)

        def from_named_dict(d):
            return [d[name] for name in FINGER_NAMES]

        if "hand_id" in config:
            new_id = config["hand_id"]
            self._protocol.write_byte(self._hand_id, REGISTERS["HAND_ID"].address, new_id)
            self._hand_id = new_id
            for finger in self._fingers:
                finger._hand_id = new_id

        if "baudrate" in config:
            baudrate = config["baudrate"]
            if baudrate in BAUD_RATE_LOOKUP:
                self._protocol.write_byte(
                    self._hand_id, REGISTERS["REDU_RATIO"].address, BAUD_RATE_LOOKUP[baudrate]
                )
                self._serial.baudrate = baudrate

        if "default_speeds" in config:
            self._protocol.write_shorts(
                self._hand_id, REGISTERS["DEFAULT_SPEED_SET"].address, from_named_dict(config["default_speeds"])
            )
        if "default_force_limits" in config:
            self._protocol.write_shorts(
                self._hand_id, REGISTERS["DEFAULT_FORCE_SET"].address, from_named_dict(config["default_force_limits"])
            )
        if "current_limits" in config:
            self._protocol.write_shorts(
                self._hand_id, REGISTERS["CURRENT_LIMIT"].address, from_named_dict(config["current_limits"])
            )
