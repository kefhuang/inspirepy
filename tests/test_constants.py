from inspirepy.constants import (
    Status,
    ErrorFlag,
    FingerName,
    BaudRate,
    FINGER_NAMES,
    JOINT_LIMITS,
    NUM_DOFS,
)


def test_status_values():
    assert Status.UNCLENCHING == 0
    assert Status.GRASPING == 1
    assert Status.TARGET_REACHED == 2
    assert Status.FORCE_LIMIT_REACHED == 3
    assert Status.CURRENT_PROTECTION == 5
    assert Status.LOCKED_ROTOR == 6
    assert Status.ACTUATOR_FAULT == 7


def test_error_flag_bits():
    assert ErrorFlag.LOCKED_ROTOR == 0x01
    assert ErrorFlag.OVER_TEMP == 0x02
    assert ErrorFlag.OVER_CURRENT == 0x04
    assert ErrorFlag.ABNORMAL_OPERATION == 0x08
    assert ErrorFlag.COMMUNICATION == 0x10


def test_finger_names_order():
    assert FINGER_NAMES == [
        "little", "ring", "middle", "index", "thumb_bend", "thumb_rotation"
    ]


def test_num_dofs():
    assert NUM_DOFS == 6


def test_baud_rate_mapping():
    assert BaudRate.B115200 == 0
    assert BaudRate.B57600 == 1
    assert BaudRate.B19200 == 2


def test_joint_limits_structure():
    assert len(JOINT_LIMITS) == 6
    for name in FINGER_NAMES:
        limits = JOINT_LIMITS[name]
        assert "min_deg" in limits
        assert "max_deg" in limits
        assert "angle_range" in limits
        assert limits["angle_range"] == (0, 1000)


def test_joint_limits_values():
    assert JOINT_LIMITS["little"]["min_deg"] == 19.0
    assert JOINT_LIMITS["little"]["max_deg"] == 176.7
    assert JOINT_LIMITS["thumb_bend"]["min_deg"] == -13.0
    assert JOINT_LIMITS["thumb_bend"]["max_deg"] == 53.6
    assert JOINT_LIMITS["thumb_rotation"]["min_deg"] == 90.0
    assert JOINT_LIMITS["thumb_rotation"]["max_deg"] == 165.0
