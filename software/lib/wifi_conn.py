
import machine
import network
import utime
import time
import socket
import struct

WiFiStatus = {
    -2: "Connection failed!",
    -1: "Access point not found!",
    0: "Idle",
    1: "Connecting...",
    2: "Wrong password",
    3: "Got IP address"
}

class wifi:
    def __init__(self):
        # Init Wi-Fi Interface
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)

    def wifi_scan(self):
        available_networks = self.wlan.scan()

        print(f"Found {len(available_networks)} wifi networks...")
        
        print("Available WiFi networks in the area:")
        for network_info in available_networks:
            print(f">> {network_info[:4]}")

    def wifi_connect( self, pwd, ssid, timeout_sec=30):
        self.wlan.connect(ssid, pwd)

        status = False
        # Wait for timeout_sec max for connection.
        while timeout_sec > 0:
            if self.wlan.status() >= 3:
                # Connection successful
                break  # the while loop
            
            time.sleep(1)  # 1 second delay
            timeout_sec -= 1
            print(f"Waiting for WiFi connection to {ssid}...")
        
        # Check if connection is successful (it may be timed out already!)
        if self.wlan.status() != 3:
            #raise RuntimeError(f"Failed to connect to {ssid} !!!")
            print(f"Wifi failed to connect...")

        else:
            print(f"Successfully connected to {ssid} at IP {self.wlan.ifconfig()[0]}...")
            status = True

        print(f" Status {self.wlan.status()}: {WiFiStatus[self.wlan.status()]}")  # prints the status to terminal for debugging

        return status

    def disconnect_wifi(self):
        """Disconnects from WiFi and disables the interface."""
        if self.wlan.isconnected():
            self.wlan.disconnect()
            self.counter_delay_loop(counter=20000)  # Give some time for disconnection
        self.wlan.active(False)  # Turn off WiFi
        print("WiFi disconnected.")

    def update_pi_localtime(self):

        timestamp = self.get_ntp_time()

        if not timestamp:
            print(f"Failed to get time from NTP.")
            return

        tm = utime.localtime(timestamp)
        rtc = machine.RTC()
        rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))  # (year, month, day, weekday, hour, min, sec, subsec)

        print("RTC set to:", utime.localtime())

    def get_pi_localtime(self):
        """Returns the local time as a formatted string."""
        tm = utime.localtime()
        print(f"Current Pi Local Time: (YYYY-MM-DD, HH:MM:SS) {tm[0]:04d}-{tm[1]:02d}-{tm[2]:02d}, {tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d}")


    def get_ntp_time(self):
        """Fetches the current time from an NTP server."""
        NTP_SERVER="pool.ntp.org"
        NTP_PORT=123
        NTP_DELTA = 2208988800  # Seconds between 1900 and 1970 (Unix time start)

        addr = socket.getaddrinfo(NTP_SERVER, NTP_PORT)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            s.settimeout(2)  # 2-second timeout
            ntp_packet = b'\x1b' + 47 * b'\0'
            s.sendto(ntp_packet, addr)
            msg, _ = s.recvfrom(48)
        except Exception as e:
            print("NTP request failed:", e)
            return None
        finally:
            s.close()

        # Extract the time from the response
        ntp_time = struct.unpack("!I", msg[40:44])[0] - NTP_DELTA  # Convert to Unix timestamp
    
        # Apply Pacific Time Zone offset
        PACIFIC_OFFSET = -8 * 3600  # PST (UTC-8)
        
        # Check if DST applies (March - November)
        local_time = utime.localtime(ntp_time)
        month, day = local_time[1], local_time[2]

        # Simple DST check: (Approximate for US, second Sunday in March to first Sunday in November)
        if (month > 3 and month < 11) or (month == 3 and day >= 8) or (month == 11 and day < 7):
            PACIFIC_OFFSET = -7 * 3600  # PDT (UTC-7)

        pacific_time = ntp_time + PACIFIC_OFFSET
        return pacific_time  # Return Pacific timestamp


    def counter_delay_loop(self, counter=1000):
        while counter:
            counter -= 1