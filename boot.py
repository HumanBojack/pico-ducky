from board import *
import digitalio
import storage

# Define the pin to check for USB drive activation
usb_activation_pin = digitalio.DigitalInOut(GP0)

# Set the pin to input mode with pull-up resistor enabled
usb_activation_pin.switch_to_input(pull=digitalio.Pull.UP)

# Check if the pin is NOT connected to ground (i.e. USB drive is not activated)
if usb_activation_pin.value:
    # Disable the USB drive
    storage.disable_usb_drive()
