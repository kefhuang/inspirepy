import struct
from unittest.mock import MagicMock, call
from inspirepy.finger import Finger
from inspirepy.constants import Status, JOINT_LIMITS


def make_finger(dof_index=3, name="index"):
    proto = MagicMock()
    finger = Finger(protocol=proto, hand_id=1, dof_index=dof_index, name=name)
    return finger, proto


def test_set_angle_absolute():
    finger, proto = make_finger()
    finger.set_angle(500)
    proto.write_shorts.assert_called_with(1, 1492, [500])


def test_set_angle_with_speed():
    finger, proto = make_finger()
    finger.set_angle(500, speed=300)
    calls = proto.write_shorts.call_args_list
    assert call(1, 1528, [300]) in calls  # SPEED_SET + 3*2
    assert call(1, 1492, [500]) in calls  # ANGLE_SET + 3*2


def test_set_angle_with_force_limit():
    finger, proto = make_finger()
    finger.set_angle(500, force_limit=200)
    calls = proto.write_shorts.call_args_list
    assert call(1, 1504, [200]) in calls  # FORCE_SET + 3*2
    assert call(1, 1492, [500]) in calls  # ANGLE_SET + 3*2


def test_set_angle_delta():
    finger, proto = make_finger()
    proto.read_shorts.return_value = [500]
    finger.set_angle(-100, delta=True)
    proto.read_shorts.assert_called_with(1, 1552, 1)  # ANGLE_ACT + 3*2
    proto.write_shorts.assert_called_with(1, 1492, [400])


def test_set_angle_delta_clamps_to_range():
    finger, proto = make_finger()
    proto.read_shorts.return_value = [50]
    finger.set_angle(-100, delta=True)
    proto.write_shorts.assert_called_with(1, 1492, [0])


def test_set_angle_delta_not_supported_for_thumb_rotation():
    finger, proto = make_finger(dof_index=5, name="thumb_rotation")
    try:
        finger.set_angle(100, delta=True)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "delta" in str(e).lower()


def test_set_position():
    finger, proto = make_finger()
    finger._set_position(1000)
    proto.write_shorts.assert_called_with(1, 1480, [1000])  # POS_SET + 3*2


def test_read_angle():
    finger, proto = make_finger()
    proto.read_shorts.return_value = [750]
    assert finger.angle == 750
    proto.read_shorts.assert_called_with(1, 1552, 1)  # ANGLE_ACT + 3*2


def test_read_position():
    finger, proto = make_finger()
    proto.read_shorts.return_value = [1500]
    assert finger.position == 1500
    proto.read_shorts.assert_called_with(1, 1540, 1)  # POS_ACT + 3*2


def test_read_force():
    finger, proto = make_finger()
    proto.read_shorts.return_value = [300]
    assert finger.force == 300
    proto.read_shorts.assert_called_with(1, 1588, 1)  # FORCE_ACT + 3*2


def test_read_current():
    finger, proto = make_finger()
    proto.read_shorts.return_value = [450]
    assert finger.current == 450
    proto.read_shorts.assert_called_with(1, 1600, 1)  # CURRENT + 3*2


def test_read_temperature():
    finger, proto = make_finger()
    proto.read_bytes.return_value = [42]
    assert finger.temperature == 42
    proto.read_bytes.assert_called_with(1, 1621, 1)  # TEMP + 3


def test_read_status():
    finger, proto = make_finger()
    proto.read_bytes.return_value = [2]
    assert finger.status == Status.TARGET_REACHED
    proto.read_bytes.assert_called_with(1, 1615, 1)  # STATUS + 3


def test_read_error():
    finger, proto = make_finger()
    proto.read_bytes.return_value = [0x06]
    error = finger.error
    assert error["locked_rotor"] is False
    assert error["over_temp"] is True
    assert error["over_current"] is True
    assert error["abnormal_operation"] is False
    assert error["communication"] is False


def test_joint_limits():
    finger, proto = make_finger(dof_index=3, name="index")
    assert finger.joint_limits == JOINT_LIMITS["index"]


def test_set_default_speed():
    finger, proto = make_finger()
    finger.set_default_speed(500)
    proto.write_shorts.assert_called_with(1, 1038, [500])  # DEFAULT_SPEED_SET + 3*2


def test_set_default_force_limit():
    finger, proto = make_finger()
    finger.set_default_force_limit(300)
    proto.write_shorts.assert_called_with(1, 1050, [300])  # DEFAULT_FORCE_SET + 3*2
