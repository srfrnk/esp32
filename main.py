import json

import machine
import neopixel
import uasyncio as asyncio

from blinds_control import BlindsController
from camera_control import CameraController


def load_calibration():
    try:
        with open("calibration.json", "r") as f:
            data = json.load(f)
            if "histogram" in data:
                return data["histogram"]
            hist = [0.0] * 256
            if "min_light" in data and "max_light" in data:
                hist[int(data["min_light"])] = 100.0
                hist[int(data["max_light"])] = 100.0
            return hist
    except Exception:
        return [0.0] * 256


def save_calibration(histogram):
    try:
        with open("calibration.json", "w") as f:
            json.dump({"histogram": histogram}, f)
    except Exception as e:
        print(f"Failed to save calibration: {e}")


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


def print_histogram_diagnostics(histogram, min_light, max_light):
    bins = 32
    bin_size = 256 // bins
    downsampled = [0.0] * bins
    for i in range(256):
        downsampled[i // bin_size] += histogram[i]
    
    max_val = max(downsampled) if max(downsampled) > 0 else 1.0
    spark_chars = " .:-=+*#%@"
    sparkline = ""
    for val in downsampled:
        idx = int((val / max_val) * (len(spark_chars) - 1))
        sparkline += spark_chars[idx]
        
    print(f"--- Diagnostics ---")
    print(f"Min: {min_light} | Max: {max_light}")
    print(f"Histogram: [{sparkline}]")
    print(f"-------------------")


async def main():
    pin = machine.Pin(48, machine.Pin.OUT)
    np = neopixel.NeoPixel(pin, 1)

    histogram = load_calibration()
    save_calibration(histogram)  # Save immediately so the file exists
    iteration_count = 0

    async with CameraController() as cam_controller:
        async with BlindsController() as blinds_controller:
            last_user_percent = None
            while True:
                light_level = cam_controller.measure_light()
                if light_level is not None:
                    print(f"Measured light level: {light_level}")
                    # Decay histogram and add current measurement
                    decay_factor = 0.9999
                    for i in range(256):
                        histogram[i] *= decay_factor

                    hist_idx = max(0, min(255, int(light_level)))
                    histogram[hist_idx] += 1.0

                    # Calculate percentiles (5th and 95th)
                    total_weight = sum(histogram)
                    min_light = None
                    max_light = 255
                    if total_weight > 0:
                        p05_threshold = total_weight * 0.05
                        p95_threshold = total_weight * 0.95
                        cumulative = 0.0
                        for i in range(256):
                            cumulative += histogram[i]
                            if min_light is None and cumulative >= p05_threshold:
                                min_light = i
                            if cumulative >= p95_threshold:
                                max_light = i
                                break
                    if min_light is None:
                        min_light = 0

                    # Periodically save calibration
                    iteration_count += 1
                    if iteration_count >= 6:
                        save_calibration(histogram)
                        iteration_count = 0
                        print(f"Saved calibration: min={min_light}, max={max_light}")
                    
                    print_histogram_diagnostics(histogram, min_light, max_light)

                    # user_percent: 0 is open, 100 is closed
                    # The darker it is, the more open it should be
                    if max_light > min_light:
                        # Enforce a minimum range so small fluctuations don't cause huge blind movements
                        range_light = max(50, max_light - min_light)
                        user_percent = max(
                            0,
                            min(100, ((light_level - min_light) / range_light) * 100.0),
                        )
                    else:
                        user_percent = max(0, min(100, (light_level / 255.0) * 100.0))
                    if (
                        last_user_percent is None
                        or abs(user_percent - last_user_percent) > 10.0
                    ):
                        await blinds_controller.set_position(user_percent)
                        last_user_percent = user_percent
                        np[0] = (0, 1, 0)
                        np.write()
                    else:
                        np[0] = (0, 0, 1)
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
