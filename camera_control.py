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
                    f.write(img[i : i + chunk_size])
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


def capture_light():
    cam = None
    try:
        # Initialize the camera. Use a small frame size and grayscale for efficient light measurement.
        cam = Camera(
            frame_size=FrameSize.QQVGA, pixel_format=PixelFormat.GRAYSCALE, init=False
        )
        cam.init()

        # The camera sensor needs frames to be processed to adjust auto-exposure and white balance.
        # We capture and discard a few initial frames to let the exposure stabilize.
        for _ in range(10):
            cam.capture()
            time.sleep(0.1)

        # Capture the final image for measurement
        img = cam.capture()

        if img:
            # The camera returns a memoryview which may iterate as signed integers.
            # Casting to bytes ensures we get unsigned values (0-255) for accurate brightness.
            img_bytes = bytes(img)
            # Calculate average pixel value for the light level
            light_level = sum(img_bytes) / len(img_bytes)
            return light_level
        else:
            print("Failed to capture image.")
            return None

    except ImportError:
        print("Camera module not available in this firmware.")
        return None
    except Exception as e:
        print(f"Error capturing light level: {e}")
        return None
    finally:
        try:
            if cam:
                cam.deinit()
        except Exception:
            pass
