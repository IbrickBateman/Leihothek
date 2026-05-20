import network
import socket
import time
import machine
import utime
import json
from mfrc522 import MFRC522

# ─── SETTINGS ───────────────────────────────────────────
WIFI_SSID = "ibo"
WIFI_PASSWORD = "malmalimal"
# ────────────────────────────────────────────────────────

# Global variable holding the last scanned tag
last_scan = {"rfid": "", "timestamp": 0}

# ─── WiFi connection ────────────────────────────────────
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    print("Connecting to WiFi", end="")
    for _ in range(50):
        if wlan.isconnected():
            break
        print(".", end="")
        time.sleep(1)
    if wlan.isconnected():
        print("\nConnected! IP:", wlan.ifconfig()[0])
        return wlan.ifconfig()[0]
    else:
        print("\nConnection failed!")
        return None

# ─── RFID reader ────────────────────────────────────────
def init_reader():
    return MFRC522(sck=2, mosi=3, miso=4, rst=0, cs=5)

def read_tag(reader):
    reader.init()
    (stat, tag_type) = reader.request(reader.REQIDL)
    if stat == reader.OK:
        (stat, uid) = reader.SelectTagSN()
        if stat == reader.OK:
            return "-".join(["%02X" % x for x in uid])
    return None

# ─── HTTP server ────────────────────────────────────────
def send_response(conn, status, content_type, body):
    response = "HTTP/1.1 {}\r\nContent-Type: {}; charset=utf-8\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}".format(
        status, content_type, len(body.encode("utf-8")), body
    )
    conn.send(response.encode("utf-8"))
    conn.close()

def start_server(ip):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((ip, 80))
    s.listen(5)
    s.setblocking(False)
    print("Server running: http://{}".format(ip))
    return s

# ─── Main loop ──────────────────────────────────────────
def main():
    ip = connect_wifi()
    if not ip:
        print("No WiFi, restarting...")
        machine.reset()

    reader = init_reader()
    server = start_server(ip)

    last_rfid = ""
    last_rfid_time = 0
    DEBOUNCE = 2000  # ms delay before same card triggers again

    print("System ready. Scan a card...")

    while True:
        # ─ Read RFID ─
        tag = read_tag(reader)
        now = utime.ticks_ms()
        if tag and (tag != last_rfid or utime.ticks_diff(now, last_rfid_time) > DEBOUNCE):
            last_rfid = tag
            last_rfid_time = now
            last_scan["rfid"] = tag
            last_scan["timestamp"] = now
            print("Card scanned:", tag)

        # ─ Handle HTTP requests ─
        try:
            conn, addr = server.accept()
            conn.setblocking(True)
            request = conn.recv(1024).decode("utf-8")
            line = request.split("\r\n")[0]
            path = line.split(" ")[1] if len(line.split(" ")) > 1 else "/"

            if path == "/last-scan":
                # Web page polls this endpoint
                data = json.dumps({
                    "rfid": last_scan["rfid"],
                    "timestamp": last_scan["timestamp"]
                })
                # Clear after sending so it does not trigger again
                last_scan["rfid"] = ""
                send_response(conn, "200 OK", "application/json", data)

            else:
                send_response(conn, "404 Not Found", "text/plain", "Not found")

        except OSError:
            pass  # No connection, normal

        utime.sleep_ms(50)

main()
