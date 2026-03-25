import struct

REQUEST_HEADER = bytes([0xEB, 0x90])
RESPONSE_HEADER = bytes([0x90, 0xEB])
READ_FLAG = 0x11
WRITE_FLAG = 0x12


class Protocol:
    def __init__(self, serial_port):
        self._serial = serial_port

    def _checksum(self, data: bytes) -> int:
        return sum(data) & 0xFF

    def _build_read_packet(self, hand_id: int, address: int, length: int) -> bytes:
        addr_l = address & 0xFF
        addr_h = (address >> 8) & 0xFF
        frame_data = bytes([hand_id, 0x04, READ_FLAG, addr_l, addr_h, length])
        cs = self._checksum(frame_data)
        return REQUEST_HEADER + frame_data + bytes([cs])

    def _build_write_packet(self, hand_id: int, address: int, data: bytes) -> bytes:
        addr_l = address & 0xFF
        addr_h = (address >> 8) & 0xFF
        frame_len = len(data) + 3
        frame_data = bytes([hand_id, frame_len, WRITE_FLAG, addr_l, addr_h]) + data
        cs = self._checksum(frame_data)
        return REQUEST_HEADER + frame_data + bytes([cs])

    def _parse_response(self, response: bytes) -> bytes:
        if len(response) < 5:
            raise ValueError(f"Response too short: {len(response)} bytes")
        if response[0:2] != RESPONSE_HEADER:
            raise ValueError(f"Invalid response header: {response[0:2].hex()}")
        expected_checksum = self._checksum(response[2:-1])
        actual_checksum = response[-1]
        if expected_checksum != actual_checksum:
            raise ValueError(
                f"Checksum mismatch: expected {expected_checksum:#x}, got {actual_checksum:#x}"
            )
        # Data starts after header(2) + id(1) + len(1) + flag(1) + addr(2) = byte 7
        return response[7:-1]

    def read_register(self, hand_id: int, address: int, length: int) -> bytes:
        packet = self._build_read_packet(hand_id, address, length)
        self._serial.write(packet)
        response_len = 2 + 1 + 1 + 1 + 2 + length + 1
        response = self._serial.read(response_len)
        return self._parse_response(response)

    def write_register(self, hand_id: int, address: int, data: bytes) -> bytes:
        packet = self._build_write_packet(hand_id, address, data)
        self._serial.write(packet)
        response_len = 9
        response = self._serial.read(response_len)
        return self._parse_response(response)

    def write_shorts(self, hand_id: int, address: int, values: list[int]) -> bytes:
        data = struct.pack(f"<{len(values)}h", *values)
        return self.write_register(hand_id, address, data)

    def read_shorts(self, hand_id: int, address: int, count: int) -> list[int]:
        raw = self.read_register(hand_id, address, count * 2)
        return list(struct.unpack(f"<{count}h", raw))

    def read_bytes(self, hand_id: int, address: int, count: int) -> list[int]:
        raw = self.read_register(hand_id, address, count)
        return list(raw)

    def write_byte(self, hand_id: int, address: int, value: int) -> bytes:
        return self.write_register(hand_id, address, bytes([value]))
