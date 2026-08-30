#!/usr/bin/env python3
"""Check the mapping logic without a controller attached.

Runs the axis maths and the report handler of powera_to_xbox.py against a
stand-in gamepad that only records what it was told to do. Nothing is opened,
no virtual pad is created, no ViGEmBus call is made -- so this is the cheap way
to see whether a change to the mapping still does what it should.

    python smoketest/smoketest.py

Exits 0 if everything passed, 1 otherwise. vgamepad still has to be installed,
because the button constants come from there.
"""

import os
import sys
from importlib.metadata import PackageNotFoundError, version

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from powera_to_xbox import (  # noqa: E402
    BUTTON_MAP_HIGH,
    BUTTON_MAP_LOW,
    HAT_MAP,
    STICK_CENTER,
    ZL_MASK,
    ZR_MASK,
    axis,
    make_handler,
)

DEADZONE = 8

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{'  -- ' + detail if detail else ''}")
        failures.append(label)


class StandInPad:
    """Records what the handler asks for, instead of talking to ViGEmBus."""

    def __init__(self):
        self.pressed = []
        self.triggers = (0, 0)
        self.left = (0, 0)
        self.right = (0, 0)
        self.updates = 0

    def reset(self):
        self.pressed = []
        self.triggers = (0, 0)

    def press_button(self, button):
        self.pressed.append(button)

    def left_trigger(self, value):
        self.triggers = (value, self.triggers[1])

    def right_trigger(self, value):
        self.triggers = (self.triggers[0], value)

    def left_joystick(self, x_value, y_value):
        self.left = (x_value, y_value)

    def right_joystick(self, x_value, y_value):
        self.right = (x_value, y_value)

    def update(self):
        self.updates += 1


def report(low=0x00, high=0x00, hat=0x08, lx=128, ly=128, rx=128, ry=128):
    """Build one raw HID report, neutral unless told otherwise."""
    return [0x00, low, high, hat, lx, ly, rx, ry]


def test_axis():
    print("axis()")
    check("centre is neutral", axis(STICK_CENTER, DEADZONE) == 0)
    check("inside the deadzone is neutral", axis(STICK_CENTER + 5, DEADZONE) == 0)
    check("the deadzone edge is still neutral", axis(STICK_CENTER + DEADZONE, DEADZONE) == 0)
    check("just outside the deadzone moves", axis(STICK_CENTER + DEADZONE + 1, DEADZONE) > 0)
    check("full right reaches the limit", axis(255, DEADZONE) == 32767)
    check("full left reaches the limit", axis(0, DEADZONE) == -32767)

    values = [axis(v, DEADZONE) for v in range(256)]
    check("monotonic across the whole range",
          all(a <= b for a, b in zip(values, values[1:])))
    check("never below -32767, so negating is safe", min(values) >= -32767,
          f"minimum was {min(values)}")
    check("stays inside the XInput range", max(values) <= 32767)
    check("deadzone 0 lets the smallest step through", axis(129, 0) != 0)


def test_buttons():
    print("buttons")
    for mask, button in BUTTON_MAP_LOW:
        pad = StandInPad()
        make_handler(pad, DEADZONE)(report(low=mask))
        check(f"byte 1 mask {mask:#04x} presses {button.name}", pad.pressed == [button],
              f"got {[b.name for b in pad.pressed]}")

    for mask, button in BUTTON_MAP_HIGH:
        pad = StandInPad()
        make_handler(pad, DEADZONE)(report(high=mask))
        check(f"byte 2 mask {mask:#04x} presses {button.name}", pad.pressed == [button],
              f"got {[b.name for b in pad.pressed]}")

    pad = StandInPad()
    make_handler(pad, DEADZONE)(report(low=ZL_MASK | ZR_MASK))
    check("ZL and ZR drive both triggers fully", pad.triggers == (255, 255),
          f"got {pad.triggers}")
    check("triggers press no buttons", pad.pressed == [])

    pad = StandInPad()
    make_handler(pad, DEADZONE)(report())
    check("a neutral report presses nothing", pad.pressed == [])
    check("a neutral report releases both triggers", pad.triggers == (0, 0))


def test_dpad():
    print("d-pad")
    for value, buttons in HAT_MAP.items():
        pad = StandInPad()
        make_handler(pad, DEADZONE)(report(hat=value))
        check(f"hat {value:#04x} gives {', '.join(b.name.split('_')[-1] for b in buttons)}",
              tuple(pad.pressed) == buttons,
              f"got {[b.name for b in pad.pressed]}")

    for value in (0x08, 0x0F, 0xFF):
        pad = StandInPad()
        make_handler(pad, DEADZONE)(report(hat=value))
        check(f"hat {value:#04x} leaves the d-pad released", pad.pressed == [])


def test_sticks():
    print("sticks")
    pad = StandInPad()
    make_handler(pad, DEADZONE)(report(ly=0, ry=0))
    check("HID up (0) becomes XInput up (positive)", pad.left[1] > 0 and pad.right[1] > 0,
          f"got left {pad.left}, right {pad.right}")

    pad = StandInPad()
    make_handler(pad, DEADZONE)(report(ly=255, ry=255))
    check("HID down (255) becomes XInput down (negative)",
          pad.left[1] < 0 and pad.right[1] < 0, f"got left {pad.left}, right {pad.right}")

    pad = StandInPad()
    make_handler(pad, DEADZONE)(report(lx=255, rx=0))
    check("X is not inverted", pad.left[0] > 0 and pad.right[0] < 0,
          f"got left {pad.left}, right {pad.right}")

    pad = StandInPad()
    make_handler(pad, DEADZONE)(report(lx=130, ly=126))
    check("a resting stick inside the deadzone reads neutral", pad.left == (0, 0),
          f"got {pad.left}")

    pad = StandInPad()
    make_handler(pad, DEADZONE)(report(lx=200, rx=200))
    check("the sticks are kept apart", pad.left != (0, 0) and pad.right != (0, 0))


def test_report_handling():
    print("report handling")
    pad = StandInPad()
    handler = make_handler(pad, DEADZONE)

    handler(report(low=0x02))
    check("a mapped press reaches the pad", len(pad.pressed) == 1)
    handler(report())
    check("releasing clears the previous press", pad.pressed == [],
          "a button would stay stuck in the game")

    before = pad.updates
    handler([0x00, 0x02, 0x00])
    check("a report shorter than 8 bytes is ignored", pad.updates == before)

    before = pad.updates
    handler(report())
    check("a full report is sent on", pad.updates == before + 1)


def main():
    try:
        vgamepad_version = version("vgamepad")
    except PackageNotFoundError:
        vgamepad_version = "not installed"
    print(f"powera-xinput smoketest, vgamepad {vgamepad_version}\n")
    test_axis()
    test_buttons()
    test_dpad()
    test_sticks()
    test_report_handling()

    print()
    if failures:
        print(f"{len(failures)} check(s) failed:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
