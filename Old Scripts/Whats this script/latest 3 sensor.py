import network
import urequests
import time
from machine import Pin, ADC, time_pulse_us

# --- 1. CONFIGURATION (CHANGE THESE!) ---
WIFI_SSID = "iPhone"
WIFI_PASS = "12345678"
THINGSPEAK_API_KEY = "GOVHFXJWRROVBY79"

# --- 2. HARDWARE SETUP (From your smart tunnel.py) ---
# Output LEDs
red_led = Pin(23, Pin.OUT)
green_led = Pin(22, Pin.OUT)

# Rain Sensor (Pin 32)
rain_sensor = ADC(Pin(32))
rain_sensor.atten(ADC.ATTN_11DB) 

# Water Level Sensor (Pin 33)
water_contact_sensor = ADC(Pin(33))
water_contact_sensor.atten(ADC.ATTN_11DB)

# Ultrasonic Sensor (Pins 27, 14)
trig = Pin(27, Pin.OUT)
echo = Pin(14, Pin.IN)

# --- 3. THRESHOLDS ---
ULTRASONIC_DANGER_CM = 15  
WATER_CONTACT_THRESHOLD = 1000 
RAIN_THRESHOLD = 2200

# --- 4. CONNECT WIFI ---
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to WiFi...', end="")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            print(".", end="")
            time.sleep(0.5)
    print('\nWiFi Connected!')

# --- 5. ULTRASONIC FUNCTION ---
def get_ultrasonic_distance():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    
    duration = time_pulse_us(echo, 1, 30000)
    
    if duration < 0:
        return 999 
    return (duration / 2) / 29.1

# --- 6. SEND TO THINGSPEAK FUNCTION ---
def send_to_cloud(dist, water, rain):
    print("Uploading to ThingSpeak...", end="")
    url = f"http://api.thingspeak.com/update?api_key={THINGSPEAK_API_KEY}&field1={dist}&field2={water}&field3={rain}"
    try:
        response = urequests.get(url)
        response.close()
        print(" Done!")
    except Exception as e:
        print(" Failed:", e)

# --- 7. MAIN LOOP ---
connect_wifi()
print("Smart Tunnel System Active...")

# Timer variable
last_upload_time = 0 

while True:
    try:
        # A. READ SENSORS
        dist_cm = get_ultrasonic_distance()
        rain_val = rain_sensor.read()
        water_val = water_contact_sensor.read()

        # B. SAFETY LOGIC (Immediate Response)
        danger_ultrasonic = (dist_cm < ULTRASONIC_DANGER_CM)
        danger_contact = (water_val > WATER_CONTACT_THRESHOLD)
        danger_rain = (rain_val < RAIN_THRESHOLD)

        if danger_ultrasonic or danger_contact or danger_rain:
            red_led.value(1)
            green_led.value(0)
            status = "DANGER"
        else:
            red_led.value(0)
            green_led.value(1)
            status = "SAFE"
            
        print(f"Status: {status} | Dist: {dist_cm:.1f}cm | Water: {water_val} | Rain: {rain_val}")

        # C. CLOUD UPLOAD (Only every 16 seconds)
        current_time = time.time()
        if current_time - last_upload_time >= 16:
            send_to_cloud(dist_cm, water_val, rain_val)
            last_upload_time = current_time

        # Short delay for stability
        time.sleep(1)

    except Exception as e:
        print("Error in loop:", e)
        time.sleep(1)