import time

from camera import Camera, FrameSize, PixelFormat


def take_snapshot(filename="snapshot.jpg"):
    cam = None
    try:
        # Initialize the camera. The pins are already pre-configured in this firmware.
        cam = Camera(
            frame_size=FrameSize.UXGA, pixel_format=PixelFormat.JPEG, init=False
        )
        cam.init()

        # Allow the camera time to adjust exposure and white balance
        time.sleep(2)

        # Capture the image
        img = cam.capture()

        if img:
            with open(filename, "wb") as f:
                # Write in chunks to prevent mpremote mount crashes over serial
                chunk_size = 4096
                for i in range(0, len(img), chunk_size):
                    f.write(img[i:i+chunk_size])
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
        except Exception:
            pass
