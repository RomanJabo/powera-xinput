#!/usr/bin/env python3
"""Map a PowerA Nintendo Switch controller onto a virtual Xbox 360 pad (XInput).

Windows exposes most PowerA wired Switch controllers as a generic DirectInput
HID device, so games that only speak XInput ignore them. This script reads the
raw HID reports and replays them on a virtual Xbox 360 controller provided by
ViGEmBus, which those games do accept.
"""

import argparse
import sys
import time

if sys.platform != "win32":
    sys.exit("This tool only runs on Windows: it needs the ViGEmBus driver.")

try:
    import pywinusb.hid as hid
except ImportError:
    sys.exit("Missing dependency 'pywinusb'. Install it with: pip install -r requirements.txt")

try:
    import vgamepad as vg
except ImportError:
    sys.exit("Missing dependency 'vgamepad'. Install it with: pip install -r requirements.txt")


POWERA_VID = 0x20D6  # Bensussen Deutsch & Associates, the maker behind PowerA

# Byte offsets inside a raw HID report. Byte 0 is the report id.
IDX_BUTTONS_LOW = 1
IDX_BUTTONS_HIGH = 2
IDX_HAT = 3
IDX_LEFT_X = 4
IDX_LEFT_Y = 5
IDX_RIGHT_X = 6
IDX_RIGHT_Y = 7
REPORT_LENGTH = 8

STICK_CENTER = 128
STICK_RANGE = 127
DEFAULT_DEADZONE = 8

# Face buttons are mapped by POSITION, not by label: the Switch layout swaps
# A/B and X/Y compared to Xbox, so the bottom button stays the bottom button.
BUTTON_MAP_LOW = (
    (0x01, vg.XUSB_BUTTON.XUSB_GAMEPAD_X),               # Switch Y (left)   -> Xbox X
    (0x02, vg.XUSB_BUTTON.XUSB_GAMEPAD_A),               # Switch B (bottom) -> Xbox A
    (0x04, vg.XUSB_BUTTON.XUSB_GAMEPAD_B),               # Switch A (right)  -> Xbox B
    (0x08, vg.XUSB_BUTTON.XUSB_GAMEPAD_Y),               # Switch X (top)    -> Xbox Y
    (0x10, vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER),   # L
    (0x20, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER),  # R
)

BUTTON_MAP_HIGH = (
    (0x01, vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK),            # minus
    (0x02, vg.XUSB_BUTTON.XUSB_GAMEPAD_START),           # plus
    (0x04, vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB),      # L3
    (0x08, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB),     # R3
)

ZL_MASK = 0x40
ZR_MASK = 0x80

# HAT switch: 0 is up, counting clockwise in 45 degree steps; 8 means centered.
HAT_MAP = {
    0x00: (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,),
    0x01: (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT),
    0x02: (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,),
    0x03: (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT),
    0x04: (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,),
    0x05: (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT),
    0x06: (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,),
    0x07: (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT),
}


def axis(value, deadzone):
    """Convert one 0..255 HID axis into the -32767..32767 XInput range.

    Values within `deadzone` units of the centre report as 0, and the range
    outside it is stretched back out so the stick still reaches full deflection.
    """
    offset = value - STICK_CENTER
    if abs(offset) <= deadzone:
        return 0
    span = STICK_RANGE - deadzone
    if span <= 0:
        return 0
    scaled = min(1.0, (abs(offset) - deadzone) / span)
    magnitude = int(scaled * 32767)
    return magnitude if offset > 0 else -magnitude


def make_handler(gamepad, deadzone, debug=False):
    """Build the callback pywinusb invokes for every incoming HID report."""

    def handler(data):
        if len(data) < REPORT_LENGTH:
            return
        if debug:
            print(" ".join(f"{b:02X}" for b in data))

        low = data[IDX_BUTTONS_LOW]
        high = data[IDX_BUTTONS_HIGH]

        gamepad.reset()

        for mask, button in BUTTON_MAP_LOW:
            if low & mask:
                gamepad.press_button(button)
        for mask, button in BUTTON_MAP_HIGH:
            if high & mask:
                gamepad.press_button(button)

        # ZL/ZR are digital on this pad, so the triggers only know 0 and full.
        gamepad.left_trigger(value=255 if low & ZL_MASK else 0)
        gamepad.right_trigger(value=255 if low & ZR_MASK else 0)

        for button in HAT_MAP.get(data[IDX_HAT], ()):
            gamepad.press_button(button)

        # HID counts Y from the top, XInput expects positive to mean up.
        gamepad.left_joystick(x_value=axis(data[IDX_LEFT_X], deadzone),
                              y_value=-axis(data[IDX_LEFT_Y], deadzone))
        gamepad.right_joystick(x_value=axis(data[IDX_RIGHT_X], deadzone),
                               y_value=-axis(data[IDX_RIGHT_Y], deadzone))

        gamepad.update()

    return handler


def find_devices(vid, pid):
    return [d for d in hid.find_all_hid_devices()
            if d.vendor_id == vid and (pid is None or d.product_id == pid)]


def list_devices():
    print("HID devices on this system:")
    for d in hid.find_all_hid_devices():
        name = d.product_name or "<unnamed>"
        print(f"  VID={d.vendor_id:#06x}  PID={d.product_id:#06x}  {name}")


def create_gamepad():
    """Create the virtual pad, or explain why ViGEmBus could not provide one."""
    try:
        return vg.VX360Gamepad()
    except Exception as exc:
        if "BUS_NOT_FOUND" in str(exc):
            print("ERROR: the ViGEmBus driver was not found.")
            print("It provides the virtual Xbox pad and has to be installed once,")
            print("as administrator, from https://github.com/nefarius/ViGEmBus/releases")
            print("Reboot afterwards if the installer asks you to.")
            return None
        raise


def hex_int(text):
    return int(text, 0)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Map a PowerA Nintendo Switch controller onto a virtual Xbox 360 pad.")
    parser.add_argument("--vid", type=hex_int, default=POWERA_VID,
                        help=f"USB vendor id, e.g. 0x20D6 (default: {POWERA_VID:#06x})")
    parser.add_argument("--pid", type=hex_int, default=None,
                        help="USB product id, e.g. 0xA711 (default: any device of that vendor)")
    parser.add_argument("--deadzone", type=int, default=DEFAULT_DEADZONE,
                        help=f"stick deadzone in raw HID units, 0-{STICK_RANGE - 1} "
                             f"(default: {DEFAULT_DEADZONE})")
    parser.add_argument("--list", action="store_true",
                        help="list every HID device with its vendor and product id, then exit")
    parser.add_argument("--debug", action="store_true",
                        help="print every raw HID report while mapping")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.list:
        list_devices()
        return 0

    if not 0 <= args.deadzone < STICK_RANGE:
        print(f"ERROR: --deadzone must be between 0 and {STICK_RANGE - 1}.")
        return 2

    matches = find_devices(args.vid, args.pid)
    if not matches:
        wanted = f"VID={args.vid:#06x}"
        if args.pid is not None:
            wanted += f" PID={args.pid:#06x}"
        print(f"ERROR: no controller found for {wanted}.")
        print("Check the USB cable, then run with --list to see every HID device")
        print("and pass the right ids with --vid / --pid.")
        return 1
    if len(matches) > 1:
        print(f"Note: {len(matches)} matching devices, using the first one. "
              f"Narrow it down with --pid.")

    controller = matches[0]
    name = controller.product_name or "<unnamed>"
    print(f"Controller: {name} "
          f"(VID={controller.vendor_id:#06x} PID={controller.product_id:#06x})")

    gamepad = create_gamepad()
    if gamepad is None:
        return 1
    print("Virtual Xbox 360 pad created.")
    print("Running - leave this window open. Press Ctrl+C to stop.\n")

    controller.open()
    controller.set_raw_data_handler(make_handler(gamepad, args.deadzone, args.debug))
    try:
        while True:
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        controller.close()
        # Release everything, so no button stays stuck in the game.
        gamepad.reset()
        gamepad.update()
    return 0


if __name__ == "__main__":
    sys.exit(main())
