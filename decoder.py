def int24_be(b: bytes):
    """3-byte big-endian, returns signed int."""
    val = int.from_bytes(b, "big", signed=False)
    return val - 0x1000000 if val & 0x800000 else val


def decode_coords(hex_str: str):
    # strip spaces, convert to bytes
    pkt = bytes.fromhex(hex_str.replace(" ", ""))
    # find the 0x25 marker (it’s always there)
    i = pkt.index(0x25) + 1
    lat_raw = int24_be(pkt[i : i + 3])  # 3 bytes
    lon_raw = int24_be(pkt[i + 3 : i + 6])  # 3 bytes
    return lat_raw / 30000, lon_raw / 30000
