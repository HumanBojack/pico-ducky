# License : GPLv2.0
# copyright (c) 2021  Dave Bailey
# Author: Dave Bailey (dbisu, @daveisu)
# TODO: Use adafruit-circuitpython-ducky ?

import usb_hid
from adafruit_hid.keyboard import Keyboard

# comment out these lines for non_US keyboards
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS as KeyboardLayout
from adafruit_hid.keycode import Keycode

# uncomment these lines for non_US keyboards
# replace LANG with appropriate language
#from keyboard_layout_win_LANG import KeyboardLayout
#from keycode_win_LANG import Keycode

import supervisor

import time
import digitalio
from digitalio import DigitalInOut, Pull
from adafruit_debouncer import Debouncer
from board import *
import asyncio


led = digitalio.DigitalInOut(LED)
led.direction = digitalio.Direction.OUTPUT

# Generate a list of aliases for the keycodes that have multiple names
aliases = {
    "APP": Keycode.APPLICATION,
    "MENU": Keycode.APPLICATION,
    "CTRL": Keycode.CONTROL,
    "DOWNARROW": Keycode.DOWN_ARROW,
    "DOWN": Keycode.DOWN_ARROW,
    "LEFTARROW": Keycode.LEFT_ARROW,
    "LEFT": Keycode.LEFT_ARROW,
    "RIGHTARROW": Keycode.RIGHT_ARROW,
    "RIGHT": Keycode.RIGHT_ARROW,
    "UPARROW": Keycode.UP_ARROW,
    "UP": Keycode.UP_ARROW,
    "BREAK": Keycode.PAUSE,
    "CAPSLOCK": Keycode.CAPS_LOCK,
    "ESC": Keycode.ESCAPE,
    "NUMLOCK": Keycode.KEYPAD_NUMLOCK,
    "PAGEUP": Keycode.PAGE_UP,
    "PAGEDOWN": Keycode.PAGE_DOWN,
    "PRINTSCREEN": Keycode.PRINT_SCREEN,
    "SCROLLLOCK": Keycode.SCROLL_LOCK,
}


def convert_line(line):
    newline = []
    # loop on each key - the filter removes empty values
    for key in filter(None, line.split(" ")):
        key = key.upper()
        # find the keycode for the command in the list
        command_keycode = aliases.get(key)
        if command_keycode:
            # if it exists in the list, use it
            newline.append(command_keycode)
        elif hasattr(Keycode, key):
            # if it's in the Keycode module, use it (allows any valid keycode)
            newline.append(getattr(Keycode, key))
        else:
            # if it's not a known key name, show the error for diagnosis
            print(f"Unknown key: <{key}>")
    return newline


# Press key(s) and release
def run_script_line(line):
    for k in line:
        keybord_device.press(k)
    keybord_device.release_all()


# Type a string
def write_string(line):
    keyboard_layout.write(line)


def parse_line(line):
    global default_delay
    if line[0:3] == "REM":
        # ignore ducky script comments
        pass
    elif line[0:5] == "DELAY":
        # Sleep for specified number of milliseconds
        time.sleep(float(line[6:]) / 1000)
    elif line[0:6] == "STRING":
        # Type the following string
        write_string(line[7:])
    elif line[0:5] == "PRINT":
        # Print the following string to the console
        print("[SCRIPT]: " + line[6:])
    elif line[0:6] == "IMPORT":
        # Import another ducky script and run it
        run_script(line[7:])
    elif line[0:13] == "DEFAULT_DELAY":
        # Set the default delay for each command
        default_delay = int(line[14:])
    elif line[0:12] == "DEFAULTDELAY":
        # Set the default delay for each command
        default_delay = int(line[13:])
    elif line[0:3] == "LED":
        # toggle the pico led
        led.value = not led.value
    else:
        # otherwise, convert the line and run it
        new_script_line = convert_line(line)
        run_script_line(new_script_line)


# init keyboard
keybord_device = Keyboard(usb_hid.devices)
keyboard_layout = KeyboardLayout(keybord_device)

# turn off automatically reloading when files are written to the pico
supervisor.disable_autoreload()

# Initialize the run button
run_button_pin = digitalio.DigitalInOut(GP22)  # Set button pin
run_button_pin.pull = digitalio.Pull.UP  # Enable internal pull-up resistor
run_button = Debouncer(run_button_pin)  # Initialize Debouncer class for button

# Initialize payload selection switches
payload_pins = [  # Create a list of payload pins
    digitalio.DigitalInOut(GP4),
    digitalio.DigitalInOut(GP5),
    digitalio.DigitalInOut(GP10),
    digitalio.DigitalInOut(GP11),
]

for pin in payload_pins:
    pin.switch_to_input(
        pull=digitalio.Pull.UP
    )  # Set each pin as input with pull-up resistor


default_delay = 0


def run_script(file):
    global default_delay

    try:
        with open(file, "r", encoding="utf-8") as f:
            previous_line = ""
            for line in f:
                line = line.rstrip()
                if line[0:6] == "REPEAT":
                    for _ in range(int(line[7:]) - 1):
                        # repeat the last command
                        parse_line(previous_line)
                        time.sleep(float(default_delay) / 1000)
                else:
                    parse_line(line)
                    previous_line = line
                time.sleep(float(default_delay) / 1000)
    except OSError:
        print("Unable to open file ", file)


def monitor_payload_selection():
    # Set default payload to "payload.dd"
    payload = None

    # Check the status of each button
    is_button1_pressed = not payload_pins[0].value
    is_button2_pressed = not payload_pins[1].value
    is_button3_pressed = not payload_pins[2].value
    is_button4_pressed = not payload_pins[3].value

    # Determine which button is pressed and set the payload accordingly
    if is_button1_pressed:
        payload = "payload.dd"
    elif is_button2_pressed:
        payload = "payload2.dd"
    elif is_button3_pressed:
        payload = "payload3.dd"
    elif is_button4_pressed:
        payload = "payload4.dd"

    if payload:
        print("Selected payload: ", payload)

    return payload


async def blink_pico_led(led):
    while True:
        led.value = not led.value
        await asyncio.sleep(1)


async def monitor_buttons(run_button):
    while True:
        button1.update()

        button1Pushed = button1.fell
        button1Released = button1.rose
        button1Held = not button1.value

        if(button1Pushed):
            print("Button 1 pushed")
            button1Down = True
        # TODO remove
        if(button1Released):
            print("Button 1 released")
            if(button1Down):
                print("push and released")

        if(button1Released):
            if(button1Down):
                # Run selected payload
                payload = selectPayload()
                print("Running ", payload)
                runScript(payload)
                print("Done")
            button1Down = False

        await asyncio.sleep(0)


async def main_loop():
    global led,button1
    pico_led_task = asyncio.create_task(blink_pico_led(led))
    button_task = asyncio.create_task(monitor_buttons(run_button))
    await asyncio.gather(pico_led_task, button_task)


asyncio.run(main_loop())
