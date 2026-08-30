# powera-xinput

Use a PowerA wired Nintendo Switch controller as an Xbox 360 controller on Windows.

Windows sees most PowerA Switch pads as a generic DirectInput HID device. Plenty of
games only listen to XInput, so the controller shows up in the system settings, moves
in the test dialog — and does nothing in the game. This script reads the raw HID
reports from the pad and replays them on a virtual Xbox 360 controller, which those
games accept.

**This is not for the Nintendo Switch Pro Controller or Joy-Cons.** Those are Nintendo
hardware (vendor id `0x057E`) speaking a different protocol — use
[BetterJoy](https://github.com/Davidobot/BetterJoy) for them. This script is for the
third-party PowerA pads (vendor id `0x20D6`), the wired ones sold as licensed Switch
accessories.

Two small files, no GUI, no background service:

| File | Purpose |
| --- | --- |
| `powera_to_xbox.py` | the mapper you run while playing |
| `read_hid.py` | diagnostic dump of raw HID reports, for adapting the mapping |

## Requirements

- Windows 10 or 11
- Python 3.9 or newer ([python.org](https://www.python.org/downloads/))
- [ViGEmBus](https://github.com/nefarius/ViGEmBus/releases) — the driver that provides
  the virtual Xbox pad
- a PowerA wired Switch controller (vendor id `0x20D6`)

## Install

1. Install ViGEmBus from the link above. It is a driver, so the installer asks for
   administrator rights, and it only has to be done once.
2. Install the Python dependencies:

   ```
   pip install -r requirements.txt
   ```

## Use

Plug the controller in, then:

```
python powera_to_xbox.py
```

Leave the window open while you play. `Ctrl+C` stops it and releases every button.

Options:

```
--vid 0x20D6      USB vendor id (default: PowerA)
--pid 0xA711      USB product id (default: any device of that vendor)
--deadzone 8      stick deadzone in raw HID units, 0-126 (default: 8)
--list            list every HID device with its ids, then exit
--debug           print every raw HID report while mapping
```

## If your controller is not found

PowerA gives each model its own product id, so yours may differ from the one this was
written against (`0xA711`). Find it:

```
python powera_to_xbox.py --list
```

Look for the entry that disappears when you unplug the pad, then pass its ids:

```
python powera_to_xbox.py --vid 0x20D6 --pid 0xA712
```

By default any device with the PowerA vendor id is accepted, so most models should
work without `--pid` at all.

## Button mapping

Face buttons are mapped **by position, not by label**. The Switch layout swaps A/B and
X/Y compared to Xbox, so the bottom button stays the bottom button and on-screen
prompts match what your thumb does.

| Switch | Xbox / XInput |
| --- | --- |
| B (bottom) | A |
| A (right) | B |
| Y (left) | X |
| X (top) | Y |
| L / R | LB / RB |
| ZL / ZR | LT / RT (digital: off or full) |
| minus / plus | Back / Start |
| L3 / R3 | Left stick / Right stick click |
| D-pad | D-pad (including diagonals) |
| Sticks | Left / Right stick |

Home and Capture are not mapped. Capture has no XInput equivalent at all. Home could
drive the Guide button (`XUSB_GAMEPAD_GUIDE`), but which bit reports it varies between
models: find it with `read_hid.py` and add it to `BUTTON_MAP_HIGH`. Note that plain
`XInputGetState` hides the Guide button, so not every game will see it.

## Sticks and deadzone

Raw sticks rest a unit or two off centre, which reads as slow drift in game. Anything
within `--deadzone` units of the centre is reported as neutral, and the range outside
it is stretched back out so the stick still reaches full deflection. Raise it if you
still drift, lower it for finer aim:

```
python powera_to_xbox.py --deadzone 12
```

## Troubleshooting

**`VIGEM_ERROR_BUS_NOT_FOUND` / "ViGEmBus driver was not found"** — install ViGEmBus and
reboot if its installer asks you to.

**The game reacts twice to one press** — Windows still sees the original DirectInput
pad alongside the new virtual one, and some games read both. In Steam, open the
controller settings and turn Steam Input off for the PowerA device.

**Buttons land in the wrong place** — your model has a different report layout. Run
`python read_hid.py`, press one button at a time, and note which byte changes and which
bit flips; then adjust `BUTTON_MAP_LOW`, `BUTTON_MAP_HIGH` and `HAT_MAP` in
`powera_to_xbox.py`. A pull request with your model and its ids is welcome.

**Nothing happens in one specific game** — check whether the game reads input only while
focused, and start the mapper before the game.

**Anti-cheat** — a virtual gamepad is a driver-level device, and some anti-cheat systems
treat that as manipulation. Do not use this in competitive online games without
checking their rules first.

## How it works

`pywinusb` opens the controller as a raw HID device and calls a handler for every
report the pad sends. The handler decodes the button bitmasks, the HAT switch and the
four stick axes, and writes them to a virtual Xbox 360 pad created through `vgamepad`,
which talks to the ViGEmBus driver. Roughly a hundred lines, meant to be read and
adapted rather than configured.

ViGEmBus emulates either an Xbox 360 pad or a DualShock 4, and the 360 one is what
Windows registers as an XInput device — exactly the interface these games are missing.
Newer Xbox controllers reach games through that same XInput API, so emulating the older
model costs nothing: the button set has not changed since 2005. Only the Series X|S
Share button and the impulse triggers live outside XInput, and neither exists on a
Switch pad anyway.

## License

MIT — see [LICENSE](LICENSE).

Not affiliated with, endorsed by or connected to Nintendo or PowerA. "Nintendo Switch"
and "PowerA" are trademarks of their respective owners and are used here only to
describe the hardware this script talks to.
