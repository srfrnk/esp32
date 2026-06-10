import time

import machine
import neopixel
import uasyncio as asyncio

from blinds_control import get_position_payload, send_blind_command
from camera_control import capture_light


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


async def main():
    for i in range(50):
        light_level = capture_light()
        print(f"Measured light level: {light_level}")
        await send_blind_command(get_position_payload(0))
        flash()
        time.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
