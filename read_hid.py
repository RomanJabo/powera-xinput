#!/usr/bin/env python3
"""Print raw HID reports from a controller, so you can work out its layout.

Use this when powera_to_xbox.py cannot find your controller, or when the
mapping is wrong for your model: press one button at a time and watch which
byte changes and which bit inside it flips. Byte 0 is the report id, so the
byte shown second is byte 1 in the script.
"""

import argparse
import sys
import time

if sys.platform != "win32":
    sys.exit("This tool only runs on Windows.")

try:
    import pywinusb.hid as hid
except ImportError:
    sys.exit("Missing dependency 'pywinusb'. Install it with: pip install -r requirements.txt")


POWERA_VID = 0x20D6


def hex_int(text):
    return int(text, 0)


def list_devices(devices):
    for d in devices:
        name = d.product_name or "<unnamed>"
        print(f"  VID={d.vendor_id:#06x}  PID={d.product_id:#06x}  {name}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Dump raw HID reports from a controller.")
    parser.add_argument("--vid", type=hex_int, default=POWERA_VID,
                        help=f"USB vendor id (default: {POWERA_VID:#06x})")
    parser.add_argument("--pid", type=hex_int, default=None,
                        help="USB product id (default: any device of that vendor)")
    parser.add_argument("--list", action="store_true",
                        help="list every HID device with its vendor and product id, then exit")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    all_devices = hid.find_all_hid_devices()

    if args.list:
        print("HID devices on this system:")
        list_devices(all_devices)
        return 0

    matches = [d for d in all_devices
               if d.vendor_id == args.vid and (args.pid is None or d.product_id == args.pid)]
    if not matches:
        wanted = f"VID={args.vid:#06x}"
        if args.pid is not None:
            wanted += f" PID={args.pid:#06x}"
        print(f"No device found for {wanted}. All HID devices:")
        list_devices(all_devices)
        return 1

    controller = matches[0]
    print(f"Found: {controller.product_name or '<unnamed>'} "
          f"(VID={controller.vendor_id:#06x} PID={controller.product_id:#06x})")
    print("Press buttons - only changed reports are printed. Ctrl+C to stop.\n")

    last = None

    def handler(data):
        nonlocal last
        if data != last:
            last = data
            print(" ".join(f"{b:02X}" for b in data))

    controller.open()
    controller.set_raw_data_handler(handler)
    try:
        while True:
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        controller.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
