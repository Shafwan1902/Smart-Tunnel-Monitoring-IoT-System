import network
import urequests
import time
from machine import Pin, ADC

# --- CONFIGURATION (CHANGE THESE) ---
WIFI_SSID = "iPhone"
WIFI_PASS = "12345678"
THINGSPEAK_API_KEY = "GOVHFXJWRROVBY79"  # <--- Paste Key Here!

# --- SENSOR PINS ---
# We use ADC.ATTN_11DB to allow reading up to 3.3V (Value 0-4095)

# 1. Rain Sensor (D32)
rain_sensor = ADC(Pin(32))
rain_sensor.atten(ADC.ATTN_11DB) 

# 2. Water Level Sensor (D33)
water_sensor = ADC(Pin(33))
water_sensor.atten(ADC.ATTN_11DB)

# 3. HW870 Soil Moisture (D35)
soil_sensor = ADC(Pin(35))
soil_sensor.atten(ADC.ATTN_11DB)

# --- CONNECT TO WIFI ---
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to WiFi...', end="")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            print(".", end="")
            time.sleep(0.5)
    print('\nWiFi Connected!', wlan.ifconfig())

# --- SEND TO THINGSPEAK ---
def send_to_cloud(val1, val2, val3):
    # Construct the URL for ThingSpeak Update
    # Field 1=Rain, Field 2=Water, Field 3=Soil
    url = f"http://api.thingspeak.com/update?api_key={THINGSPEAK_API_KEY}&field1={val1}&field2={val2}&field3={val3}"
    
    try:
        response = urequests.get(url)
        print(f"Uploaded: Rain={val1}, Water={val2}, Soil={val3}")
        print("Server Reply:", response.text) # A number (entry ID) means success
        response.close()
    except Exception as e:
        print("Upload Failed:", e)

# --- MAIN LOOP ---
connect_wifi()
print("System Running... Press Ctrl+C to Stop")

while True:
    try:
        # 1. Read Raw Sensor Data (0-4095)
        # Note: Rain and Soil sensors often read HIGH (4095) when DRY 
        # and LOW (0) when WET. This is normal.
        r_val = rain_sensor.read()
        w_val = water_sensor.read()
        s_val = soil_sensor.read()

        # 2. Send Data
        send_to_cloud(r_val, w_val, s_val)
        
        # 3. Wait 16 Seconds
        # ThingSpeak Free Tier requires 15 seconds between updates
        time.sleep(16) 
        
    except KeyboardInterrupt:
        break
    except Exception as e:
        print("Loop Error:", e)
        time.sleep(5)