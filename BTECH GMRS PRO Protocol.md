# BTECH GMRS‑PRO / UV‑PRO **BSS** Protocol Cheat‑Sheet

_Last updated 2025‑06‑22_

---

## 1  Overview

BTECH’s GMRS‑PRO (and dual‑band UV‑PRO) hand‑helds can exchange short data bursts that carry **GPS fixes, text messages, altitude, speed, and status flags**.
On‑air they use **1200 baud AFSK (Bell 202 tones) wrapped in an AX.25 HDLC frame**, but with proprietary addressing—BTECH calls this the **“BSS” mode**. When the radio is switched to Amateur‑APRS mode it transmits normal AX.25, but in GMRS/BSS mode the header bytes differ so that ordinary APRS gear ignores them.

Three distinct BSS packet flavours have been captured so far:

| ID                  | Trigger                | Main payload      | Leading control bytes                                          |
| ------------------- | ---------------------- | ----------------- | -------------------------------------------------------------- |
| **Manual point‑at** | _Send Location_ button | GPS only          | `05 05`                                                        |
| **Auto beacon**     | PTT **release**        | GPS + alt + speed | long header `01 8B 00 00 F9 2D 05` **or** short header `01 05` |
| **Text + GPS**      | App‐typed message      | ASCII text + GPS  | `01 05` … `$ … \x07`                                           |

All three share the same GPS encoding (**‘%’ marker + 6 bytes**) and the same 2‑byte CRC‑16/X‑25 footer.

---

## 2  Byte‑Level Anatomy

### 2.1 Header / AX.25 address block

- 0–5 bytes   → **Destination & source fields**. In GMRS/BSS these are binary IDs, not human callsigns.
- 6 th byte    → **Packet‑type** (`0x05`, `0x0D` …).
- Optional space `0x20` before callsign.

> **Fingerprinting:** the 7‑byte AX.25 source address (6 shifted ASCII + SSID) uniquely identifies a handset even if its on‑screen name changes.

### 2.2 Callsign string

ASCII between the first space (`0x20`) and the record separator (`0x0D`). Can include spaces, e.g. `"Alex Malcolm"`.

### 2.3 GPS + telemetry block

```
0x25                                    # '%' start‑of‑GPS
[0:3]  lat_int24_be / 30 000            # ±90°
[3:6]  lon_int24_be / 30 000            # ±180°
[6:8]  altitude_m_u16_be                # metres
[8:10] speed_raw_u16_be / 10 → km/h    # 0.1 km/h resolution
[10:12]  2‑byte flags / ACK field       # values seen: FF FF, 00 FE, 00 7A …
```

- **Signed‑24‑bit** integers are two’s‑complement, big‑endian. 1 LSb = 1⁄30 000°. <br>Resolution ≈ 3.3 m at the equator.
- Altitude fits 0–65535 m (≈ 215 k ft).

### 2.4 Footer

- **CRC‑16/X‑25** (poly 0x1021, init 0xFFFF, reflected, xorout 0xFFFF) sent **little‑endian**.

---

## 3  Quick‑Reference Decoder (Python ≥ 3.8)

```python
from typing import Dict

def _i24(b: bytes) -> int:
    n = int.from_bytes(b, 'big'); return n-0x1000000 if n & 0x800000 else n

def decode_any_beacon(raw_hex: str) -> Dict[str, object]:
    p = bytes.fromhex(raw_hex.replace(' ', ''))
    spc = p.index(0x20)
    rs  = p.index(0x0D, spc+1)
    name = p[spc+1:rs].decode('ascii').strip()

    # optional 7‑byte AX.25 source
    src = p[spc-7:spc] if spc >= 7 else None

    if p[rs+1] != 0x25:
        raise ValueError('GPS marker missing')
    g = rs+2
    lat = _i24(p[g:g+3])/30000
    lon = _i24(p[g+3:g+6])/30000
    alt = int.from_bytes(p[g+6:g+8], 'big')
    spd = int.from_bytes(p[g+8:g+10],'big')/10
    flg = p[g+10:g+12].hex()
    return dict(callsign=name, lat=lat, lon=lon, alt_m=alt,
                speed_kmh=spd, flags=flg,
                ax25_src=src.hex() if src else None)
```

---

## 4  Packet Builder (Tx)

_Multiply degrees by 30 000 → 24‑bit signed, big‑endian._
Combine with the appropriate header, text block, and CRC. Full reference implementation lives in **`btech_builder.py`** (see previous messages).

---

## 5  Common Flag Values

| Flags   | Meaning (observed)                |
| ------- | --------------------------------- |
| `FF FF` | normal auto‑beacon w/ ACK request |
| `00 FE` | no‑ACK / low‑battery?             |
| `00 7A` | long‑name variant                 |
| `00 55` | second radio (Vuth)               |

Understanding of the two‑byte flag field is still incomplete.

---

## 6  Transmitting From a Computer

1. **Run Direwolf** with `MODEM 1200`, `PTT VOX`, `KISSPORT 8001`.
2. Build a raw frame with `btech_builder.py` functions.
3. Wrap in KISS (`0xC0 0x00 … 0xC0`) and send via TCP 8001.
4. Direwolf modulates 1200 AFSK → audio → VOX keys radio.

---

## 7  Open Questions

- Full definition of the 2‑byte flag / ACK field.
- Whether other telemetry (heading, battery, sat‑count) can be enabled.
- How group/team IDs map to the AX.25 destination address.

Community contributions welcome—please fork & PR!
