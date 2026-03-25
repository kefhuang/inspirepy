import yaml
from unittest.mock import MagicMock, call
from inspirepy.sequence import ActionSequence
from inspirepy.constants import FINGER_NAMES


def make_sequence(slot=0):
    proto = MagicMock()
    seq = ActionSequence(protocol=proto, hand_id=1, slot=slot)
    return seq, proto


def test_add_step():
    seq, proto = make_sequence()
    seq.add_step(angles=[0, 0, 0, 0, 0, 0], speed=500, force_limit=300, duration=500)
    assert len(seq._steps) == 1


def test_add_step_max_8():
    seq, proto = make_sequence()
    for i in range(8):
        seq.add_step(angles=[0]*6, speed=500, force_limit=300, duration=100)
    try:
        seq.add_step(angles=[0]*6, speed=500, force_limit=300, duration=100)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "8" in str(e)


def test_upload():
    seq, proto = make_sequence(slot=0)
    seq.add_step(angles=[100, 200, 300, 400, 500, 600], speed=500, force_limit=300, duration=1000)
    seq.add_step(angles=[600, 500, 400, 300, 200, 100], speed=800, force_limit=200, duration=500)
    seq.upload()
    calls = proto.write_byte.call_args_list
    assert call(1, 2320, 0) in calls  # ACTION_SEQ_INDEX
    assert call(1, 2002, 2) in calls  # ACTION_SEQ_STEPNUM
    assert call(1, 2000, 0x90) in calls  # CHECK_DATA1
    assert call(1, 2001, 0xEB) in calls  # CHECK_DATA2
    assert call(1, 2321, 1) in calls  # SAVE_ACTION_SEQ
    assert proto.write_shorts.call_count == 2


def test_run():
    seq, proto = make_sequence(slot=3)
    seq.add_step(angles=[0]*6, speed=500, force_limit=300, duration=100)
    seq.upload()
    proto.write_byte.reset_mock()
    seq.run()
    calls = proto.write_byte.call_args_list
    assert call(1, 2320, 3) in calls
    assert call(1, 2322, 1) in calls


def test_save_yaml(tmp_path):
    seq, proto = make_sequence()
    seq.add_step(angles=[0, 0, 0, 0, 0, 0], speed=500, force_limit=300, duration=500)
    seq.add_step(angles=[1000, 1000, 1000, 1000, 1000, 500], speed=500, force_limit=300, duration=300)
    path = tmp_path / "wave.yaml"
    seq.save(str(path))
    with open(path) as f:
        data = yaml.safe_load(f)
    assert len(data["steps"]) == 2
    assert data["steps"][0]["angles"]["little"] == 0
    assert data["steps"][0]["speed"] == 500


def test_load_yaml(tmp_path):
    data = {
        "steps": [
            {
                "angles": {"little": 0, "ring": 0, "middle": 0, "index": 0, "thumb_bend": 0, "thumb_rotation": 0},
                "speed": 500, "force_limit": 300, "duration": 500,
            },
            {
                "angles": {"little": 1000, "ring": 1000, "middle": 1000, "index": 1000, "thumb_bend": 1000, "thumb_rotation": 500},
                "speed": 800, "force_limit": 200, "duration": 300,
            },
        ]
    }
    path = tmp_path / "wave.yaml"
    with open(path, "w") as f:
        yaml.dump(data, f)
    proto = MagicMock()
    seq = ActionSequence.load(str(path), protocol=proto, hand_id=1, slot=0)
    assert len(seq._steps) == 2
    assert seq._steps[0]["angles"] == [0, 0, 0, 0, 0, 0]
    assert seq._steps[1]["angles"] == [1000, 1000, 1000, 1000, 1000, 500]
