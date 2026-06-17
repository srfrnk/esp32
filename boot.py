import time
import network
import json

def connect_wifi():
    try:
        with open("wifi_secrets.json", "r") as f:
            secrets = json.load(f)
            ssid = secrets.get("ssid", "")
            password = secrets.get("password", "")
            hostname = secrets.get("hostname", None)
    except Exception:
        print("wifi_secrets.json not found or invalid.")
        return False

    if not ssid or ssid == "YOUR_WIFI_SSID":
        print("No valid SSID configured in wifi_secrets.json.")
        return False

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if hostname:
        wlan.config(dhcp_hostname=hostname)
        print(f"Hostname set to: {hostname}")
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
        ip = wlan.ifconfig()[0]
        print("Wi-Fi connected!")
        print("IP Address:", ip)
        print(f"Dashboard (via Wi-Fi): http://{ip}/")
        return True

def start_access_point():
    ap_ssid = "ESP-Blinds"
    ap_password = "blinds_admin"
    enable_ap = True
    try:
        with open("wifi_secrets.json", "r") as f:
            import json
            secrets = json.load(f)
            ap_ssid = secrets.get("ap_ssid", ap_ssid)
            ap_password = secrets.get("ap_password", ap_password)
            enable_ap = secrets.get("enable_ap", True)
    except Exception:
        pass

    ap = network.WLAN(network.AP_IF)
    if not enable_ap:
        # Do NOT call ap.active(False) — on MicroPython this can disrupt the
        # shared lwIP TCP/IP stack and prevent the STA interface from accepting
        # connections, even when the server binds to 0.0.0.0.
        print("Access Point disabled by configuration.")
        print("Dashboard is still available via Wi-Fi IP above.")
        return False

    ap.active(True)
    ap.config(essid=ap_ssid, password=ap_password, authmode=3)
    ap_ip = ap.ifconfig()[0]
    print("Access Point broadcast started!")
    print("AP IP Address:", ap_ip)
    print(f"Dashboard (via AP):      http://{ap_ip}/")
    return True

# 1. Connect to the guest network for internet access
connect_wifi()

# 2. Start the Access Point for direct Dashboard access
start_access_point()

