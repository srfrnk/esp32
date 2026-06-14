import uasyncio as asyncio
import json
import esp32
from config import APP_CONFIG

try:
    import urequests as requests
except ImportError:
    import requests

class TemperatureSensor:
    def __init__(self, secrets_file="wifi_secrets.json"):
        self.secrets_file = secrets_file
        # Defaults, can be overridden in wifi_secrets.json
        self.api_key = "YOUR_OPENWEATHERMAP_API_KEY"
        self.location_query = "London,UK"
        self.calibration_offset = 0.0
        self.is_calibrated = False
        
        self.load_config()
        self.load_saved_calibration()

    def load_saved_calibration(self):
        try:
            with open("temp_calibration.json", "r") as f:
                data = json.load(f)
                if "offset" in data:
                    self.calibration_offset = float(data["offset"])
                    self.is_calibrated = True
                    print(f"Temperature Sensor: Loaded saved offset: {self.calibration_offset:.2f} °C")
        except Exception:
            pass

    def save_calibration(self):
        try:
            with open("temp_calibration.json", "w") as f:
                json.dump({"offset": self.calibration_offset}, f)
        except Exception as e:
            print(f"Temperature Sensor: Failed to save calibration: {e}")

    def load_config(self):
        try:
            with open(self.secrets_file, "r") as f:
                secrets = json.load(f)
                self.api_key = secrets.get("owm_api_key", self.api_key)
                self.location_query = secrets.get("location_query", self.location_query)
        except Exception as e:
            print(f"TemperatureSensor: Could not load config: {e}")

    async def get_real_temperature(self, max_retries=3):
        if self.api_key == "YOUR_OPENWEATHERMAP_API_KEY":
            print("Temperature Sensor: Missing OpenWeatherMap API Key in wifi_secrets.json (owm_api_key)")
            return None
        # Using http:// instead of https:// to prevent SSL/TLS handshake connection resets (-104) on the ESP32
        url = f"http://api.openweathermap.org/data/2.5/weather?q={self.location_query}&appid={self.api_key}&units=metric"
        
        for attempt in range(max_retries):
            try:
                # Added a timeout so a bad network connection doesn't block the entire uasyncio event loop
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    temp = data['main']['temp']
                    response.close()
                    return temp
                else:
                    print(f"Temperature Sensor: Error fetching weather: HTTP {response.status_code}")
                    response.close()
            except Exception as e:
                print(f"Temperature Sensor: Exception fetching weather (Attempt {attempt + 1}/{max_retries}): {e}")
                
            if attempt < max_retries - 1:
                await asyncio.sleep(5)  # Wait 5 seconds before retrying

        return None

    def get_internal_temperature(self):
        try:
            return esp32.mcu_temperature()
        except AttributeError:
            try:
                temp_f = esp32.raw_temperature()
                return (temp_f - 32.0) / 1.8
            except Exception as e:
                print(f"Temperature Sensor: Could not read internal temperature sensor: {e}")
                return None

    async def calibration_task(self):
        while True:
            print("Temperature Sensor: Running calibration task...")
            real_temp = await self.get_real_temperature()
            internal_temp = self.get_internal_temperature()
            if real_temp is not None and internal_temp is not None:
                self.calibration_offset = real_temp - internal_temp
                self.is_calibrated = True
                self.save_calibration()
                print(f"Temperature Sensor: Calibrated. Offset: {self.calibration_offset:.2f} °C")
            
            # Recalibrate every configured interval
            await asyncio.sleep(APP_CONFIG.timing.temperature_recalibration_interval)

    def get_estimated_temperature(self):
        internal_temp = self.get_internal_temperature()
        if internal_temp is not None:
            return internal_temp + self.calibration_offset
        return None
