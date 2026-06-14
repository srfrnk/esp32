import network
import time
import json
import esp32
import requests # Make sure urequests or requests is available

# --- Configuration ---
WIFI_SECRETS_FILE = "wifi_secrets.json"

# OpenWeatherMap API Configuration
OWM_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"
# Set your location (e.g., London)
LAT = "51.5074"
LON = "-0.1278"

# ---------------------

def connect_wifi():
    """Connects to WiFi using credentials from secrets file."""
    with open(WIFI_SECRETS_FILE, 'r') as f:
        secrets = json.load(f)
        
    ssid = secrets.get('ssid')
    password = secrets.get('password')
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(0.5)
            print('.', end='')
    print('\nNetwork connected!')
    print('IP address:', wlan.ifconfig()[0])

def get_real_temperature():
    """Fetches the current temperature in Celsius from OpenWeatherMap."""
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric"
    print("Fetching weather data...")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = data['main']['temp']
            response.close()
            return temp
        else:
            print(f"Error fetching weather: HTTP {response.status_code}")
            response.close()
            return None
    except Exception as e:
        print("Exception fetching weather:", e)
        return None

def get_internal_temperature():
    """Reads the internal MCU temperature in Celsius."""
    try:
        # ESP32-S3 specific method (available in newer MicroPython builds)
        return esp32.mcu_temperature()
    except AttributeError:
        # Fallback for classic ESP32 (returns Fahrenheit, so we convert)
        try:
            temp_f = esp32.raw_temperature()
            temp_c = (temp_f - 32.0) / 1.8
            return temp_c
        except Exception as e:
            print("Could not read internal temperature sensor:", e)
            return None

def main():
    connect_wifi()
    
    # 1. Get real ambient temperature
    real_ambient_temp = get_real_temperature()
    if real_ambient_temp is None:
        print("Failed to get calibration temperature. Exiting.")
        return
        
    print(f"Real Ambient Temperature (API): {real_ambient_temp:.2f} °C")
    
    # 2. Get internal ESP32 temperature
    internal_temp = get_internal_temperature()
    if internal_temp is None:
        return
        
    print(f"Raw Internal Temperature: {internal_temp:.2f} °C")
    
    # 3. Calculate the offset
    # Because internal_temp = ambient_temp + self_heating
    # offset = ambient_temp - internal_temp (will be negative usually)
    calibration_offset = real_ambient_temp - internal_temp
    print(f"Calculated Calibration Offset: {calibration_offset:.2f} °C")
    
    # 4. Continuous monitoring loop
    print("\nStarting continuous monitoring. Press Ctrl+C to stop.")
    while True:
        current_internal = get_internal_temperature()
        estimated_ambient = current_internal + calibration_offset
        print(f"Internal: {current_internal:.1f} °C | Estimated Ambient: {estimated_ambient:.1f} °C")
        time.sleep(5)

if __name__ == "__main__":
    main()
