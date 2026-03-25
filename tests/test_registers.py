from inspirepy.registers import Register, REGISTERS


def test_hand_id_register():
    r = REGISTERS["HAND_ID"]
    assert r.address == 1000
    assert r.length == 1
    assert r.writable is True


def test_angle_set_register():
    r = REGISTERS["ANGLE_SET"]
    assert r.address == 1486
    assert r.length == 12
    assert r.writable is True


def test_angle_act_register():
    r = REGISTERS["ANGLE_ACT"]
    assert r.address == 1546
    assert r.length == 12
    assert r.writable is False


def test_pos_set_register():
    r = REGISTERS["POS_SET"]
    assert r.address == 1474
    assert r.length == 12
    assert r.writable is True


def test_temp_register():
    r = REGISTERS["TEMP"]
    assert r.address == 1618
    assert r.length == 6
    assert r.writable is False


def test_error_register():
    r = REGISTERS["ERROR"]
    assert r.address == 1606
    assert r.length == 6
    assert r.writable is False


def test_status_register():
    r = REGISTERS["STATUS"]
    assert r.address == 1612
    assert r.length == 6
    assert r.writable is False


def test_voltage_register():
    r = REGISTERS["VLTAGE"]
    assert r.address == 1472
    assert r.length == 2
    assert r.writable is False


def test_action_seq_step_registers():
    for i in range(8):
        r = REGISTERS[f"ACTION_SEQ_STEP_{i}"]
        assert r.address == 2016 + i * 38
        assert r.length == 38
        assert r.writable is True


def test_action_seq_control_registers():
    assert REGISTERS["ACTION_SEQ_INDEX"].address == 2320
    assert REGISTERS["ACTION_SEQ_RUN"].address == 2322
    assert REGISTERS["SAVE_ACTION_SEQ"].address == 2321
    assert REGISTERS["ACTION_SEQ_STEPNUM"].address == 2002
    assert REGISTERS["ACTION_SEQ_CHECK_DATA1"].address == 2000
    assert REGISTERS["ACTION_SEQ_CHECK_DATA2"].address == 2001


def test_all_registers_have_required_fields():
    for name, r in REGISTERS.items():
        assert isinstance(r.address, int), f"{name} missing address"
        assert isinstance(r.length, int), f"{name} missing length"
        assert isinstance(r.writable, bool), f"{name} missing writable"
