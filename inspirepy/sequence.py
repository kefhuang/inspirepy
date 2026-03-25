import yaml
from inspirepy.constants import FINGER_NAMES, NUM_DOFS
from inspirepy.registers import REGISTERS


class ActionSequence:
    MAX_STEPS = 8

    def __init__(self, protocol, hand_id: int, slot: int = 0):
        self._protocol = protocol
        self._hand_id = hand_id
        self._slot = slot
        self._steps = []

    def add_step(self, angles: list, speed: int, force_limit: int, duration: int):
        if len(self._steps) >= self.MAX_STEPS:
            raise ValueError(f"Maximum {self.MAX_STEPS} steps per sequence")
        if len(angles) != NUM_DOFS:
            raise ValueError(f"Expected {NUM_DOFS} angles, got {len(angles)}")
        self._steps.append({
            "angles": list(angles),
            "speed": speed,
            "force_limit": force_limit,
            "duration": duration,
        })

    def _encode_step(self, step: dict) -> list:
        angles = step["angles"]
        speeds = [step["speed"]] * NUM_DOFS
        force_limits = [step["force_limit"]] * NUM_DOFS
        duration = step["duration"]
        return angles + speeds + force_limits + [duration]

    def upload(self):
        self._protocol.write_byte(self._hand_id, REGISTERS["ACTION_SEQ_INDEX"].address, self._slot)
        for i, step in enumerate(self._steps):
            step_data = self._encode_step(step)
            self._protocol.write_shorts(self._hand_id, REGISTERS[f"ACTION_SEQ_STEP_{i}"].address, step_data)
        self._protocol.write_byte(self._hand_id, REGISTERS["ACTION_SEQ_STEPNUM"].address, len(self._steps))
        self._protocol.write_byte(self._hand_id, REGISTERS["ACTION_SEQ_CHECK_DATA1"].address, 0x90)
        self._protocol.write_byte(self._hand_id, REGISTERS["ACTION_SEQ_CHECK_DATA2"].address, 0xEB)
        self._protocol.write_byte(self._hand_id, REGISTERS["SAVE_ACTION_SEQ"].address, 1)

    def run(self):
        self._protocol.write_byte(self._hand_id, REGISTERS["ACTION_SEQ_INDEX"].address, self._slot)
        self._protocol.write_byte(self._hand_id, REGISTERS["ACTION_SEQ_RUN"].address, 1)

    def save(self, path: str):
        def to_named_dict(values):
            return {name: val for name, val in zip(FINGER_NAMES, values)}
        data = {
            "steps": [
                {
                    "angles": to_named_dict(step["angles"]),
                    "speed": step["speed"],
                    "force_limit": step["force_limit"],
                    "duration": step["duration"],
                }
                for step in self._steps
            ]
        }
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @classmethod
    def load(cls, path: str, protocol, hand_id: int, slot: int = 0) -> "ActionSequence":
        with open(path) as f:
            data = yaml.safe_load(f)
        seq = cls(protocol=protocol, hand_id=hand_id, slot=slot)
        for step_data in data["steps"]:
            angles_dict = step_data["angles"]
            angles = [angles_dict[name] for name in FINGER_NAMES]
            seq.add_step(
                angles=angles,
                speed=step_data["speed"],
                force_limit=step_data["force_limit"],
                duration=step_data["duration"],
            )
        return seq
