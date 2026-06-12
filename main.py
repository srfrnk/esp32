import json
import time
import ntptime

import machine
import neopixel
import uasyncio as asyncio

from blinds_control import BlindsController
from camera_control import CameraController
from web_server.server import start_server

diagnostics_data = {
    "light_level": None,
    "min_light": None,
    "max_light": None,
    "user_percent": None,
    "target_light": 90.0,
    "histogram_sparkline": ""
}


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


def get_histogram_sparkline(histogram):
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

    return sparkline


async def sync_time_task():
    while True:
        try:
            print("Synchronizing time with NTP...")
            ntptime.settime()  # Sets RTC to UTC
            
            utc_seconds = time.time()
            t = time.localtime(utc_seconds)
            year, month, day, hour = t[0], t[1], t[2], t[3]
            
            # UK DST is from the last Sunday of March to the last Sunday of October
            is_bst = False
            if 3 < month < 10:
                is_bst = True
            elif month == 3 or month == 10:
                last_sunday = 31
                for d in range(31, 24, -1):
                    if time.localtime(time.mktime((year, month, d, 0, 0, 0, 0, 0)))[6] == 6:
                        last_sunday = d
                        break
                if month == 3 and (day > last_sunday or (day == last_sunday and hour >= 1)):
                    is_bst = True
                elif month == 10 and (day < last_sunday or (day == last_sunday and hour < 1)):
                    is_bst = True
            
            offset = 3600 if is_bst else 0
            local_seconds = utc_seconds + offset
            lt = time.localtime(local_seconds)
            
            # Update RTC to local time: (year, month, day, weekday, hours, minutes, seconds, subseconds)
            machine.RTC().datetime((lt[0], lt[1], lt[2], lt[6], lt[3], lt[4], lt[5], 0))
            
            tz_name = "BST" if is_bst else "GMT"
            print(f"Time synchronized ({tz_name}): {lt[0]:04d}-{lt[1]:02d}-{lt[2]:02d} {lt[3]:02d}:{lt[4]:02d}:{lt[5]:02d}")
        except Exception as e:
            print(f"Failed to synchronize time: {e}")
        # Sync every 1 hour
        await asyncio.sleep(3600)


async def main():
    pin = machine.Pin(48, machine.Pin.OUT)
    np = neopixel.NeoPixel(pin, 1)

    try:
        await start_server(diagnostics_data, "0.0.0.0", 80)
    except Exception as e:
        print(f"Failed to start HTTP server: {e}")

    # Start the background time synchronization task
    asyncio.create_task(sync_time_task())

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

                    sparkline = get_histogram_sparkline(histogram)
                    print("--- Diagnostics ---")
                    print(f"Min: {min_light} | Max: {max_light}")
                    print(f"Histogram: [{sparkline}]")
                    print("-------------------")
                    
                    diagnostics_data["min_light"] = min_light
                    diagnostics_data["max_light"] = max_light
                    diagnostics_data["histogram_sparkline"] = sparkline
                    diagnostics_data["light_level"] = light_level

                    # TARGET_LIGHT is the desired brightness in the room.
                    # We use an incremental controller to seek this target, which is robust
                    # against ambient light changes (like room lights being turned on).
                    TARGET_LIGHT = 90.0
                    DEADBAND = 4.0  # Allowable +/- drift before moving blinds

                    if last_user_percent is None:
                        # On first run, we just pick a middle ground or use the min/max logic
                        user_percent = 50.0
                    else:
                        if light_level > TARGET_LIGHT + DEADBAND:
                            # Too bright -> close blinds
                            error = light_level - TARGET_LIGHT
                            # Proportional step: bigger error = bigger step, max 15% per iteration
                            step = min(15.0, max(2.0, error * 0.5))
                            user_percent = min(100.0, last_user_percent + step)
                        elif light_level < TARGET_LIGHT - DEADBAND:
                            # Too dark -> open blinds
                            error = TARGET_LIGHT - light_level
                            step = min(15.0, max(2.0, error * 0.5))
                            user_percent = max(0.0, last_user_percent - step)
                        else:
                            # Within target range, don't move
                            user_percent = last_user_percent

                    diagnostics_data["user_percent"] = user_percent
                    diagnostics_data["target_light"] = TARGET_LIGHT

                    if (
                        last_user_percent is None
                        or abs(user_percent - last_user_percent) >= 2.0
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
