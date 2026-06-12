import time
import network
import json

def connect_wifi():
    try:
        with open("wifi_secrets.json", "r") as f:
            secrets = json.load(f)
            ssid = secrets.get("ssid", "")
            password = secrets.get("password", "")
    except Exception:
        print("wifi_secrets.json not found or invalid.")
        return False

    if not ssid or ssid == "YOUR_WIFI_SSID":
        print("No valid SSID configured in wifi_secrets.json.")
        return False

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f"Connecting to Wi-Fi network: {ssid}...")
        wlan.connect(ssid, password)
        
        # Wait up to 10 seconds for connection
        max_wait = 10
        while max_wait > 0:
            if wlan.isconnected():
                break
            max_wait -= 1
            print("Waiting for connection...")
            time.sleep(1)

    if not wlan.isconnected():
        print(f"Wi-Fi connection failed. Status: {wlan.status()}")
        return False
    else:
        print("Wi-Fi connected!")
        print("IP Address:", wlan.ifconfig()[0])
        return True

def start_access_point():
    ap_ssid = "ESP-Blinds"
    ap_password = "blinds_admin"
    try:
        with open("wifi_secrets.json", "r") as f:
            import json
            secrets = json.load(f)
            ap_ssid = secrets.get("ap_ssid", ap_ssid)
            ap_password = secrets.get("ap_password", ap_password)
    except Exception:
        pass

    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ap_ssid, password=ap_password, authmode=3)
    print("Access Point broadcast started!")
    print("AP IP Address:", ap.ifconfig()[0])
    return True

# 1. Connect to the guest network for internet access
connect_wifi()

# 2. Start the Access Point for direct Dashboard access
start_access_point()

