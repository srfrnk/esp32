import machine
import neopixel
import uasyncio as asyncio

from blinds_control import BlindsController
from camera_control import CameraController


async def flash():
    # Pin 48 is the built-in RGB NeoPixel (WS2812) on the ESP32-S3-CAM
    pin = machine.Pin(48, machine.Pin.OUT)
    np = neopixel.NeoPixel(pin, 1)

    for i in range(2):
        np[0] = (1, 0, 0)
        np.write()
        await asyncio.sleep(0.1)
        np[0] = (0, 0, 1)
        np.write()
        await asyncio.sleep(0.1)
        np[0] = (0, 1, 0)
        np.write()
        await asyncio.sleep(0.1)

    np[0] = (0, 0, 0)
    np.write()


print("Boot script running successfully!")


async def main():
    pin = machine.Pin(48, machine.Pin.OUT)
    np = neopixel.NeoPixel(pin, 1)

    async with CameraController() as cam_controller:
        async with BlindsController() as blinds_controller:
            while True:
                light_level = cam_controller.measure_light()
                if light_level is not None:
                    print(f"Measured light level: {light_level}")
                    # light_level is 0 (dark) to 255 (bright)
                    # user_percent: 0 is open, 100 is closed
                    # The darker it is, the more open it should be
                    user_percent = max(0, min(100, (light_level / 255.0) * 100.0))
                    await blinds_controller.set_position(user_percent)
                    np[0] = (0, 1, 0)
                    np.write()
                else:
                    print("Failed to measure light level.")
                    np[0] = (1, 0, 0)
                    np.write()
                await asyncio.sleep(0.1)
                np[0] = (0, 0, 0)
                np.write()
                await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
