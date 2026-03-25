from typing import Optional
from inspirepy.constants import Status, ErrorFlag, JOINT_LIMITS
from inspirepy.registers import REGISTERS


class Finger:
    def __init__(self, protocol, hand_id: int, dof_index: int, name: str):
        self._protocol = protocol
        self._hand_id = hand_id
        self._dof_index = dof_index
        self._name = name

    def _short_addr(self, register_name: str) -> int:
        return REGISTERS[register_name].address + self._dof_index * 2

    def _byte_addr(self, register_name: str) -> int:
        return REGISTERS[register_name].address + self._dof_index

    def set_angle(self, value: int, *, delta: bool = False,
                  speed: Optional[int] = None, force_limit: Optional[int] = None):
        if delta:
            if self._name == "thumb_rotation":
                raise ValueError("delta mode is not supported for thumb_rotation (DOF 5)")
            current = self._protocol.read_shorts(self._hand_id, self._short_addr("ANGLE_ACT"), 1)[0]
            value = max(0, min(1000, current + value))

        if speed is not None:
            self._protocol.write_shorts(self._hand_id, self._short_addr("SPEED_SET"), [speed])
        if force_limit is not None:
            self._protocol.write_shorts(self._hand_id, self._short_addr("FORCE_SET"), [force_limit])

        self._protocol.write_shorts(self._hand_id, self._short_addr("ANGLE_SET"), [value])

    def _set_position(self, value: int):
        self._protocol.write_shorts(self._hand_id, self._short_addr("POS_SET"), [value])

    def set_default_speed(self, value: int):
        self._protocol.write_shorts(self._hand_id, self._short_addr("DEFAULT_SPEED_SET"), [value])

    def set_default_force_limit(self, value: int):
        self._protocol.write_shorts(self._hand_id, self._short_addr("DEFAULT_FORCE_SET"), [value])

    @property
    def angle(self) -> int:
        return self._protocol.read_shorts(self._hand_id, self._short_addr("ANGLE_ACT"), 1)[0]

    @property
    def position(self) -> int:
        return self._protocol.read_shorts(self._hand_id, self._short_addr("POS_ACT"), 1)[0]

    @property
    def force(self) -> int:
        return self._protocol.read_shorts(self._hand_id, self._short_addr("FORCE_ACT"), 1)[0]

    @property
    def current(self) -> int:
        return self._protocol.read_shorts(self._hand_id, self._short_addr("CURRENT"), 1)[0]

    @property
    def temperature(self) -> int:
        return self._protocol.read_bytes(self._hand_id, self._byte_addr("TEMP"), 1)[0]

    @property
    def status(self):
        raw = self._protocol.read_bytes(self._hand_id, self._byte_addr("STATUS"), 1)[0]
        try:
            return Status(raw)
        except ValueError:
            return raw

    @property
    def error(self) -> dict:
        raw = self._protocol.read_bytes(self._hand_id, self._byte_addr("ERROR"), 1)[0]
        return {
            "locked_rotor": bool(raw & ErrorFlag.LOCKED_ROTOR),
            "over_temp": bool(raw & ErrorFlag.OVER_TEMP),
            "over_current": bool(raw & ErrorFlag.OVER_CURRENT),
            "abnormal_operation": bool(raw & ErrorFlag.ABNORMAL_OPERATION),
            "communication": bool(raw & ErrorFlag.COMMUNICATION),
        }

    @property
    def joint_limits(self) -> dict:
        return JOINT_LIMITS[self._name]
