import uasyncio as asyncio
from camera import Camera, FrameSize, PixelFormat


class CameraController:
    def __init__(self):
        self._cam = None

    async def __aenter__(self):
        # Initialize the camera. The `Camera` constructor automatically initializes the hardware.
        self._cam = Camera(
            frame_size=FrameSize.QQVGA, pixel_format=PixelFormat.GRAYSCALE
        )

        # The camera sensor needs frames to be processed to adjust auto-exposure and white balance.
        # We capture and discard a few initial frames to let the exposure stabilize.
        for _ in range(10):
            self._cam.capture()
            await asyncio.sleep(0.1)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._cam is not None:
            try:
                self._cam.deinit()
            except Exception:
                pass
            self._cam = None

    def measure_light(self):
        if self._cam is None:
            print(
                "Camera is not initialized. Make sure to use the 'with' context manager."
            )
            return None

        try:
            # Flush one frame to ensure we get the most recent reading, not a stale buffered one
            self._cam.capture()

            # Capture the final image for measurement
            img = self._cam.capture()

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

        except Exception as e:
            print(f"Error capturing light level: {e}")
            return None
