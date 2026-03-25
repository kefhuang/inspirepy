from unittest.mock import MagicMock, call
from inspirepy.protocol import Protocol


def make_protocol(response_bytes=b""):
    serial_mock = MagicMock()
    serial_mock.read.return_value = response_bytes
    proto = Protocol(serial_mock)
    return proto, serial_mock


def test_checksum_calculation():
    proto, _ = make_protocol()
    # Checksum is low byte of sum of all bytes
    assert proto._checksum(bytes([0x01, 0x04, 0x11, 0x0A, 0x06, 0x0C])) == 0x32


def test_build_read_packet():
    proto, _ = make_protocol()
    # Read ANGLE_ACT (address=1546=0x060A, length=12=0x0C) for hand_id=1
    packet = proto._build_read_packet(hand_id=1, address=1546, length=12)
    assert packet[0] == 0xEB  # header
    assert packet[1] == 0x90  # header
    assert packet[2] == 0x01  # hand_id
    assert packet[3] == 0x04  # frame data length
    assert packet[4] == 0x11  # read flag
    assert packet[5] == 0x0A  # address low byte
    assert packet[6] == 0x06  # address high byte
    assert packet[7] == 0x0C  # register length
    assert packet[8] == proto._checksum(packet[2:8])


def test_build_write_packet():
    proto, _ = make_protocol()
    # Write single byte (value=1) to RESET_PARA (address=1006=0x03EE) for hand_id=1
    data = bytes([0x01])
    packet = proto._build_write_packet(hand_id=1, address=1006, data=data)
    assert packet[0] == 0xEB
    assert packet[1] == 0x90
    assert packet[2] == 0x01  # hand_id
    assert packet[3] == 0x04  # frame data length: len(data) + 3
    assert packet[4] == 0x12  # write flag
    assert packet[5] == 0xEE  # address low byte (1006 & 0xFF)
    assert packet[6] == 0x03  # address high byte (1006 >> 8)
    assert packet[7] == 0x01  # data
    assert packet[8] == proto._checksum(packet[2:8])


def test_build_write_packet_multi_byte():
    proto, _ = make_protocol()
    import struct
    data = struct.pack("<6h", 100, 100, 100, 100, 1000, 0)
    packet = proto._build_write_packet(hand_id=1, address=1486, data=data)
    assert packet[0] == 0xEB
    assert packet[1] == 0x90
    assert packet[2] == 0x01
    assert packet[3] == 15  # 12 + 3
    assert packet[4] == 0x12
    assert packet[5] == 0xCE  # address low
    assert packet[6] == 0x05  # address high
    assert len(packet) == 2 + 1 + 1 + 1 + 2 + 12 + 1  # header(2) + id + len + flag + addr(2) + data(12) + checksum


def test_parse_read_response():
    proto, _ = make_protocol()
    # Response for reading 6 shorts, all value 100
    response = bytes([
        0x90, 0xEB,  # response header
        0x01,        # hand_id
        0x0F,        # length: 12 + 3
        0x11,        # read response flag
        0x0A, 0x06,  # address
        0x64, 0x00, 0x64, 0x00, 0x64, 0x00,  # 100, 100, 100
        0x64, 0x00, 0x64, 0x00, 0x64, 0x00,  # 100, 100, 100
    ])
    checksum = proto._checksum(response[2:])
    response = response + bytes([checksum])
    data = proto._parse_response(response)
    assert data == bytes([0x64, 0x00] * 6)


def test_parse_write_response():
    proto, _ = make_protocol()
    response = bytes([
        0x90, 0xEB,
        0x01,        # hand_id
        0x04,        # length
        0x12,        # write response flag
        0xCE, 0x05,  # address
        0x01,        # success
    ])
    checksum = proto._checksum(response[2:])
    response = response + bytes([checksum])
    data = proto._parse_response(response)
    assert data == bytes([0x01])


def test_read_register_sends_and_receives():
    proto, serial_mock = make_protocol()
    response = bytes([
        0x90, 0xEB,
        0x01,  # hand_id
        0x04,  # length: 1 + 3
        0x11,  # read flag
        0xE8, 0x03,  # address 1000
        0x01,  # data: id=1
    ])
    checksum = proto._checksum(response[2:])
    response = response + bytes([checksum])
    serial_mock.read.return_value = response

    result = proto.read_register(hand_id=1, address=1000, length=1)
    serial_mock.write.assert_called_once()
    assert result == bytes([0x01])
