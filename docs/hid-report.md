# HID report reference

*[Deutsche Fassung](hid-report.de.md)*

What a PowerA wired Switch pad puts on the wire, and how `powera_to_xbox.py` reads it.
Statements marked *measured* were verified on real hardware: one PowerA wired
controller, vendor id `0x20D6`, product id `0xA711`, over USB on Windows 11.

---

## The device

| | |
|---|---|
| Vendor id | `0x20D6` — Bensussen Deutsch & Associates, the company behind the PowerA brand |
| Product id | `0xA711` *(measured — other PowerA models use different ids)* |
| Transport | wired USB |
| Class | USB HID, generic gamepad |
| What Windows does with it | binds it to DirectInput. It appears in `joy.cpl` and moves in the test dialog, but no XInput device is created — which is why XInput-only games do not see it. |

The pad sends an input report on every state change. `pywinusb` hands that report to a
callback as a list of byte values.

## Report layout

Byte 0 is the report id, so the first payload byte is byte 1. This script reads bytes 1
through 7 and ignores anything beyond; the full report is longer, and its remaining
bytes have not been examined.

| Byte | Contents |
|---|---|
| 0 | report id |
| 1 | face and shoulder buttons, bitmask *(measured)* |
| 2 | menu and stick buttons, bitmask *(measured)* |
| 3 | D-pad as a HAT switch value *(measured)* |
| 4 | left stick X *(measured)* |
| 5 | left stick Y *(measured)* |
| 6 | right stick X *(measured)* |
| 7 | right stick Y *(measured)* |

### Byte 1 — face and shoulder buttons

| Mask | Switch button | Mapped to |
|---|---|---|
| `0x01` | Y (left) | `XUSB_GAMEPAD_X` |
| `0x02` | B (bottom) | `XUSB_GAMEPAD_A` |
| `0x04` | A (right) | `XUSB_GAMEPAD_B` |
| `0x08` | X (top) | `XUSB_GAMEPAD_Y` |
| `0x10` | L | `XUSB_GAMEPAD_LEFT_SHOULDER` |
| `0x20` | R | `XUSB_GAMEPAD_RIGHT_SHOULDER` |
| `0x40` | ZL | left trigger, 0 or 255 |
| `0x80` | ZR | right trigger, 0 or 255 |

The face buttons are deliberately **not** mapped by label. Nintendo places B at the
bottom and A on the right, Microsoft the other way round, so mapping by position keeps
the on-screen prompt and the thumb in agreement.

ZL and ZR are plain switches on this pad, not analog. The triggers therefore only ever
report 0 or 255 — a game with a gradual throttle will feel like an on/off pedal, and
that is the hardware, not the mapping.

### Byte 2 — menu and stick buttons

| Mask | Switch button | Mapped to |
|---|---|---|
| `0x01` | minus | `XUSB_GAMEPAD_BACK` |
| `0x02` | plus | `XUSB_GAMEPAD_START` |
| `0x04` | L3 (left stick click) | `XUSB_GAMEPAD_LEFT_THUMB` |
| `0x08` | R3 (right stick click) | `XUSB_GAMEPAD_RIGHT_THUMB` |
| `0x10` – `0x80` | **not examined** | — |

Home and Capture were not traced. They are the obvious candidates for the four unused
high bits of this byte, but that is a guess, not a measurement. If you find them, Home
can be mapped to `XUSB_GAMEPAD_GUIDE`; Capture has no XInput equivalent.

### Byte 3 — D-pad

A standard 8-direction HAT switch, counting clockwise from up in 45° steps:

| Value | Direction | Value | Direction |
|---|---|---|---|
| `0x00` | up | `0x04` | down |
| `0x01` | up + right | `0x05` | down + left |
| `0x02` | right | `0x06` | left |
| `0x03` | down + right | `0x07` | up + left |

Centred is reported as `0x08` by convention. The script does not test for it: any value
outside 0–7 falls through the lookup and leaves the D-pad released, which handles the
centre value and any unexpected one alike.

### Bytes 4–7 — analog sticks

| | |
|---|---|
| Range | 0–255, one byte per axis *(measured)* |
| Centre | 128 |
| X | 0 = full left, 255 = full right |
| Y | **0 = up**, 255 = down *(measured)* |

The Y direction is the one detail that catches people out. HID counts down the screen,
XInput counts up, so both Y axes are negated on the way through:

```python
gamepad.left_joystick(x_value=axis(data[4], deadzone),
                      y_value=-axis(data[5], deadzone))
```

`axis()` converts 0–255 into XInput's −32767…32767, applies the deadzone around the
centre, and stretches what is left back out to the full range so the stick still
reaches its limits. It never returns −32768, which is what makes the negation above
safe.

## Measuring your own pad

If your model reports differently, `read_hid.py` is the way to find out how:

```
python read_hid.py
```

It prints one line per changed report, as hex bytes. Then:

1. **Do nothing first.** The line you see at rest is your baseline. Note what the stick
   bytes read when centred — if they are not 128, that is exactly the drift the
   deadzone is there to absorb.
2. **Press one button at a time**, and compare against the baseline. One bit will flip.
   The byte position and the bit give you a row for `BUTTON_MAP_LOW` or
   `BUTTON_MAP_HIGH`.
3. **Roll the D-pad around** its eight directions and read off byte 3.
4. **Push each stick to its limits** to confirm the axis order and which end is which.

Remember the offset: the second value printed is byte 1, because byte 0 is the report
id.

A pull request adding your model — its product id and anything that differed — is
welcome.
