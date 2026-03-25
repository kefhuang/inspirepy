import yaml
from unittest.mock import patch, MagicMock
from inspirepy.hand import InspireHand


@patch("inspirepy.hand.serial.Serial")
@patch("inspirepy.hand.Protocol")
def make_hand(MockProtocol, MockSerial):
    proto = MockProtocol.return_value
    hand = InspireHand("/dev/ttyUSB0")
    return hand, proto


def test_save_config(tmp_path):
    hand, proto = make_hand()
    proto.read_shorts.side_effect = [
        [500, 500, 500, 500, 500, 500],
        [300, 300, 300, 300, 300, 300],
        [1500, 1500, 1500, 1500, 1500, 1500],
    ]
    proto.read_bytes.side_effect = [
        [1],
        [0],
    ]
    path = tmp_path / "config.yaml"
    hand.save_config(str(path))
    with open(path) as f:
        config = yaml.safe_load(f)
    assert config["hand_id"] == 1
    assert config["baudrate"] == 115200
    assert config["default_speeds"]["little"] == 500
    assert config["default_force_limits"]["little"] == 300
    assert config["current_limits"]["little"] == 1500


def test_load_config(tmp_path):
    hand, proto = make_hand()
    config = {
        "hand_id": 2,
        "baudrate": 115200,
        "default_speeds": {
            "little": 400, "ring": 400, "middle": 400,
            "index": 400, "thumb_bend": 400, "thumb_rotation": 400,
        },
        "default_force_limits": {
            "little": 250, "ring": 250, "middle": 250,
            "index": 250, "thumb_bend": 250, "thumb_rotation": 250,
        },
        "current_limits": {
            "little": 1000, "ring": 1000, "middle": 1000,
            "index": 1000, "thumb_bend": 1000, "thumb_rotation": 1000,
        },
    }
    path = tmp_path / "config.yaml"
    with open(path, "w") as f:
        yaml.dump(config, f)
    hand.load_config(str(path))
    proto.write_byte.assert_any_call(1, 1000, 2)
    proto.write_shorts.assert_any_call(2, 1032, [400, 400, 400, 400, 400, 400])
    proto.write_shorts.assert_any_call(2, 1044, [250, 250, 250, 250, 250, 250])
    proto.write_shorts.assert_any_call(2, 1020, [1000, 1000, 1000, 1000, 1000, 1000])


def test_save_config_uses_finger_names(tmp_path):
    hand, proto = make_hand()
    proto.read_shorts.side_effect = [
        [100, 200, 300, 400, 500, 600],
        [100, 200, 300, 400, 500, 600],
        [100, 200, 300, 400, 500, 600],
    ]
    proto.read_bytes.side_effect = [
        [1],
        [0],
    ]
    path = tmp_path / "config.yaml"
    hand.save_config(str(path))
    with open(path) as f:
        config = yaml.safe_load(f)
    for section in ["default_speeds", "default_force_limits", "current_limits"]:
        assert "little" in config[section]
        assert "thumb_rotation" in config[section]
