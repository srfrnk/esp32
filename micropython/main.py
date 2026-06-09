import time

import machine
import neopixel

# Pin 48 is the built-in RGB NeoPixel (WS2812) on the ESP32-S3-CAM
pin = machine.Pin(48, machine.Pin.OUT)
np = neopixel.NeoPixel(pin, 1)

print("Boot script running successfully!")
print(machine.freq())
print("Blinking NeoPixel LED every 0.5 seconds...")

for i in range(2):
    np[0] = (50, 0, 0)
    np.write()
    time.sleep(0.5)
    np[0] = (0, 0, 50)
    np.write()
    time.sleep(0.5)
    np[0] = (0, 50, 0)
    np.write()
    time.sleep(0.5)
np[0] = (0, 0, 0)
np.write()
