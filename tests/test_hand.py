import struct
from unittest.mock import MagicMock, patch, call
from inspirepy.hand import InspireHand
from inspirepy.constants import FINGER_NAMES, JOINT_LIMITS


@patch("inspirepy.hand.serial.Serial")
@patch("inspirepy.hand.Protocol")
def make_hand(MockProtocol, MockSerial):
    proto_instance = MockProtocol.return_value
    serial_instance = MockSerial.return_value
    # factory_reset writes to RESET_PARA
    hand = InspireHand("/dev/ttyUSB0")
    proto_instance.write_byte.assert_called_with(1, 1006, 1)
    return hand, proto_instance


def test_init_factory_resets():
    hand, proto = make_hand()
    proto.write_byte.assert_called_with(1, 1006, 1)


def test_finger_attributes_exist():
    hand, proto = make_hand()
    assert hand.little._dof_index == 0
    assert hand.ring._dof_index == 1
    assert hand.middle._dof_index == 2
    assert hand.index._dof_index == 3
    assert hand.thumb_bend._dof_index == 4
    assert hand.thumb_rotation._dof_index == 5


def test_set_angles_bulk():
    hand, proto = make_hand()
    hand.set_angles([100, 200, 300, 400, 500, 600])
    proto.write_shorts.assert_any_call(1, 1486, [100, 200, 300, 400, 500, 600])


def test_set_angles_with_speed_single():
    hand, proto = make_hand()
    hand.set_angles([500, 500, 500, 500, 500, 500], speed=300)
    proto.write_shorts.assert_any_call(1, 1522, [300, 300, 300, 300, 300, 300])


def test_set_angles_with_speed_list():
    hand, proto = make_hand()
    speeds = [100, 200, 300, 400, 500, 600]
    hand.set_angles([500, 500, 500, 500, 500, 500], speed=speeds)
    proto.write_shorts.assert_any_call(1, 1522, speeds)


def test_set_angles_with_force_limit_single():
    hand, proto = make_hand()
    hand.set_angles([500, 500, 500, 500, 500, 500], force_limit=200)
    proto.write_shorts.assert_any_call(1, 1498, [200, 200, 200, 200, 200, 200])


def test_set_angles_delta():
    hand, proto = make_hand()
    proto.read_shorts.return_value = [500, 500, 500, 500, 500, 500]
    hand.set_angles([-100, -100, -100, -100, -100, -100], delta=True)
    proto.read_shorts.assert_called_with(1, 1546, 6)
    proto.write_shorts.assert_any_call(1, 1486, [400, 400, 400, 400, 400, 400])


def test_get_angles():
    hand, proto = make_hand()
    proto.read_shorts.return_value = [100, 200, 300, 400, 500, 600]
    result = hand.get_angles()
    proto.read_shorts.assert_called_with(1, 1546, 6)
    assert result == [100, 200, 300, 400, 500, 600]


def test_get_forces():
    hand, proto = make_hand()
    proto.read_shorts.return_value = [10, 20, 30, 40, 50, 60]
    result = hand.get_forces()
    proto.read_shorts.assert_called_with(1, 1582, 6)
    assert result == [10, 20, 30, 40, 50, 60]


def test_get_currents():
    hand, proto = make_hand()
    proto.read_shorts.return_value = [100, 200, 300, 400, 500, 600]
    result = hand.get_currents()
    proto.read_shorts.assert_called_with(1, 1594, 6)
    assert result == [100, 200, 300, 400, 500, 600]


def test_get_temperatures():
    hand, proto = make_hand()
    proto.read_bytes.return_value = [30, 31, 32, 33, 34, 35]
    result = hand.get_temperatures()
    proto.read_bytes.assert_called_with(1, 1618, 6)
    assert result == [30, 31, 32, 33, 34, 35]


def test_get_statuses():
    hand, proto = make_hand()
    proto.read_bytes.return_value = [0, 1, 2, 3, 5, 6]
    result = hand.get_statuses()
    proto.read_bytes.assert_called_with(1, 1612, 6)
    assert len(result) == 6


def test_get_errors():
    hand, proto = make_hand()
    proto.read_bytes.return_value = [0, 0, 0x06, 0, 0, 0]
    result = hand.get_errors()
    proto.read_bytes.assert_called_with(1, 1606, 6)
    assert len(result) == 6


def test_voltage():
    hand, proto = make_hand()
    proto.read_shorts.return_value = [2400]
    assert hand.voltage == 2400
    proto.read_shorts.assert_called_with(1, 1472, 1)


def test_joint_limits():
    hand, proto = make_hand()
    limits = hand.joint_limits
    assert len(limits) == 6
    for name in FINGER_NAMES:
        assert name in limits
        assert limits[name] == JOINT_LIMITS[name]


def test_set_default_speeds_single():
    hand, proto = make_hand()
    hand.set_default_speeds(500)
    proto.write_shorts.assert_any_call(1, 1032, [500, 500, 500, 500, 500, 500])


def test_set_default_speeds_list():
    hand, proto = make_hand()
    speeds = [100, 200, 300, 400, 500, 600]
    hand.set_default_speeds(speeds)
    proto.write_shorts.assert_any_call(1, 1032, speeds)


def test_set_default_force_limits_single():
    hand, proto = make_hand()
    hand.set_default_force_limits(300)
    proto.write_shorts.assert_any_call(1, 1044, [300, 300, 300, 300, 300, 300])


def test_clear_errors():
    hand, proto = make_hand()
    hand.clear_errors()
    proto.write_byte.assert_called_with(1, 1004, 1)


def test_calibrate_force_sensors():
    hand, proto = make_hand()
    hand.calibrate_force_sensors()
    proto.write_byte.assert_called_with(1, 1009, 1)


def test_set_id():
    hand, proto = make_hand()
    hand.set_id(5)
    proto.write_byte.assert_called_with(1, 1000, 5)
    assert hand._hand_id == 5


def test_set_baudrate():
    hand, proto = make_hand()
    hand.set_baudrate(57600)
    proto.write_byte.assert_called_with(1, 1002, 1)  # BaudRate.B57600 == 1


def test_context_manager():
    with patch("inspirepy.hand.serial.Serial") as MockSerial, \
         patch("inspirepy.hand.Protocol"):
        with InspireHand("/dev/ttyUSB0") as hand:
            assert hand is not None
        MockSerial.return_value.close.assert_called_once()
