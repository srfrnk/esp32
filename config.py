import json
import sys

class LightControlConfig:
    def __init__(self, data):
        self.target = data["target"]
        self.deadband = data["deadband"]
        self.initial_user_percent = data["initial_user_percent"]

class ServerConfig:
    def __init__(self, data):
        self.ip = data["ip"]
        self.port = data["port"]

class TimingConfig:
    def __init__(self, data):
        self.ntp_sync_interval = data["ntp_sync_interval"]
        self.loop_sleep_time = data["loop_sleep_time"]
        self.temperature_recalibration_interval = data["temperature_recalibration_interval"]

class HardwareConfig:
    def __init__(self, data):
        self.neopixel_pin = data["neopixel_pin"]

class CameraConfig:
    def __init__(self, data):
        self.aec_value = data["aec_value"]
        self.agc_gain = data["agc_gain"]

class BlindsConfig:
    def __init__(self, data):
        self.mac_addr = data["mac_addr"]

class AppConfig:
    def __init__(self, filename="config.json"):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to load {filename}: {e}")
            sys.exit(1)

        try:
            self.light_control = LightControlConfig(data["light_control"])
            self.server = ServerConfig(data["server"])
            self.timing = TimingConfig(data["timing"])
            self.hardware = HardwareConfig(data["hardware"])
            self.camera = CameraConfig(data["camera"])
            self.blinds = BlindsConfig(data["blinds"])
        except KeyError as e:
            print(f"CRITICAL ERROR: Missing required config key in {filename}: {e}")
            sys.exit(1)

APP_CONFIG = AppConfig()
