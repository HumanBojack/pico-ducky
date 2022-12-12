from board import *
import digitalio
import storage

# Only activate the usb_drive if the GP0 pin is connected
progStatusPin = digitalio.DigitalInOut(GP0)
progStatusPin.switch_to_input(pull=digitalio.Pull.UP)
if progStatusPin.value:
    storage.disable_usb_drive()