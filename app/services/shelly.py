import requests

def get_shelly_status():
    url = "http://192.168.33.1/rpc/Switch.GetStatus?id=0"

    try:
        data = requests.get(url, timeout=2).json()
        power = data.get("apower", 0)

        if power > 1:
            status = "Working"
            color = "#22c55e"
        elif power > 0.2:
            status = "Standby"
            color = "#facc15"
        else:
            status = "Not working"
            color = "#ef4444"

    except Exception:
        power = 0
        status = "No connection"
        color = "#9ca3af"

    return {
        "power": power,
        "status": status,
        "color": color
    }