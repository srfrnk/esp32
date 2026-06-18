import time

import machine
import neopixel
import ntptime
import uasyncio as asyncio

from blinds_control import BlindsController
from camera_control import CameraController
from config import APP_CONFIG
from temperature_sensor import TemperatureSensor
from web_server.server import start_server

diagnostics_data = {
    "light_level": None,
    "user_percent": None,
    "target_light": APP_CONFIG.light_control.target,
    "temperature": None,
}


async def flash():
    # Pin is the built-in RGB NeoPixel
    pin = machine.Pin(APP_CONFIG.hardware.neopixel_pin, machine.Pin.OUT)
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


async def sync_time_task():
    # Set a 10-second timeout for NTP to prevent hanging
    if hasattr(ntptime, "timeout"):
        ntptime.timeout = 10

    while True:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(
                    f"Synchronizing time with NTP... (Attempt {attempt + 1}/{max_retries})"
                )
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
                        if (
                            time.localtime(
                                time.mktime((year, month, d, 0, 0, 0, 0, 0))
                            )[6]
                            == 6
                        ):
                            last_sunday = d
                            break
                    if month == 3 and (
                        day > last_sunday or (day == last_sunday and hour >= 1)
                    ):
                        is_bst = True
                    elif month == 10 and (
                        day < last_sunday or (day == last_sunday and hour < 1)
                    ):
                        is_bst = True

                offset = 3600 if is_bst else 0
                local_seconds = utc_seconds + offset
                lt = time.localtime(local_seconds)

                # Update RTC to local time: (year, month, day, weekday, hours, minutes, seconds, subseconds)
                machine.RTC().datetime(
                    (lt[0], lt[1], lt[2], lt[6], lt[3], lt[4], lt[5], 0)
                )

                tz_name = "BST" if is_bst else "GMT"
                print(
                    f"Time synchronized ({tz_name}): {lt[0]:04d}-{lt[1]:02d}-{lt[2]:02d} {lt[3]:02d}:{lt[4]:02d}:{lt[5]:02d}"
                )
                break  # Success! Break out of the retry loop.
            except Exception as e:
                print(f"Failed to synchronize time: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)  # Wait 5 seconds before retrying

        # Sync at configured interval
        await asyncio.sleep(APP_CONFIG.timing.ntp_sync_interval)


async def main():
    pin = machine.Pin(APP_CONFIG.hardware.neopixel_pin, machine.Pin.OUT)
    np = neopixel.NeoPixel(pin, 1)

    try:
        await start_server(
            diagnostics_data, APP_CONFIG.server.ip, APP_CONFIG.server.port
        )
    except Exception as e:
        print(f"Failed to start HTTP server: {e}")

    # Start the background time synchronization task
    asyncio.create_task(sync_time_task())

    # Initialize temperature sensor and start its background calibration task
    temp_sensor = TemperatureSensor()
    asyncio.create_task(temp_sensor.calibration_task())

    print("Device is ready! Flashing LED...")
    await flash()

    async with CameraController() as cam_controller:
        async with BlindsController() as blinds_controller:
            last_user_percent = None
            while True:
                light_level = cam_controller.measure_light()
                if light_level is not None:
                    print(f"Measured light level: {light_level}")
                    estimated_temp = temp_sensor.get_estimated_temperature()

                    print("--- Diagnostics ---")
                    if estimated_temp is not None:
                        print(f"Temperature: {estimated_temp:.1f} °C")
                    else:
                        print("Temperature: Not Available")
                    print("-------------------")

                    diagnostics_data["light_level"] = light_level
                    diagnostics_data["temperature"] = estimated_temp

                    # TARGET_LIGHT is the desired brightness in the room.
                    # We use an incremental controller to seek this target, which is robust
                    # against ambient light changes (like room lights being turned on).
                    TARGET_LIGHT = APP_CONFIG.light_control.target
                    DEADBAND = (
                        APP_CONFIG.light_control.deadband
                    )  # Allowable +/- drift before moving blinds

                    if last_user_percent is None:
                        # On first run, we just pick a middle ground or use the min/max logic
                        user_percent = APP_CONFIG.light_control.initial_user_percent
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
                await asyncio.sleep(APP_CONFIG.timing.loop_sleep_time)


if __name__ == "__main__":
    asyncio.run(main())
