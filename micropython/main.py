import time
from camera import Camera, FrameSize, PixelFormat  # type: ignore

import machine
import neopixel


def flash():
    # Pin 48 is the built-in RGB NeoPixel (WS2812) on the ESP32-S3-CAM
    pin = machine.Pin(48, machine.Pin.OUT)
    np = neopixel.NeoPixel(pin, 1)

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


def take_snapshot(filename="snapshot.jpg"):
    cam = None
    try:
        # Initialize the camera. The pins are already pre-configured in this firmware.
        cam = Camera(
            frame_size=FrameSize.VGA, pixel_format=PixelFormat.JPEG, init=False
        )
        cam.init()

        # Allow the camera time to adjust exposure and white balance
        time.sleep(2)

        # Capture the image
        img = cam.capture()

        if img:
            with open(filename, "wb") as f:
                f.write(img)
            print(f"Snapshot saved as {filename}")
            return True
        else:
            print("Failed to capture image.")
            return False

    except ImportError:
        print("Camera module not available in this firmware.")
        return False
    except Exception as e:
        print(f"Error taking snapshot: {e}")
        return False
    finally:
        try:
            if cam:
                cam.deinit()
        except:
            pass


print("Boot script running successfully!")
take_snapshot()
