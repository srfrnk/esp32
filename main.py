import time

import machine
import neopixel

from camera_control import take_snapshot

def flash():
    # Pin 48 is the built-in RGB NeoPixel (WS2812) on the ESP32-S3-CAM
    pin = machine.Pin(48, machine.Pin.OUT)
    np = neopixel.NeoPixel(pin, 1)

    for i in range(3):
        np[0] = (50, 0, 0)
        np.write()
        time.sleep(0.1)
        np[0] = (0, 0, 50)
        np.write()
        time.sleep(0.1)
        np[0] = (0, 50, 0)
        np.write()
        time.sleep(0.1)

    np[0] = (0, 0, 0)
    np.write()


print("Boot script running successfully!")
take_snapshot()
()
flash()
