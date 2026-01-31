import network
import time
import machine
import dht
import urequests  # Must be installed via Thonny
from machine import Pin, ADC

# ==========================================
# CONFIGURATION
# ==========================================
WIFI_SSID = "iPhone"
WIFI_PASS = "12345678"
THINGSPEAK_API_KEY = "GOVHFXJWRROVBY79"
THINGSPEAK_URL = "http://api.thingspeak.com/update"

# ==========================================
# HARDWARE SETUP (PIN MAPPING)
# ==========================================

# 1. DHT22 (Temp/Hum) -> GPIO 21
dht_sensor = dht.DHT22(Pin(21))

# 2. LDR (Light) -> GPIO 34 (ADC)
ldr_pin = ADC(Pin(34))
ldr_pin.atten(ADC.ATTN_11DB)  # Allows reading up to ~3.3V
ldr_pin.width(ADC.WIDTH_12BIT)  # 0 - 4095 range

# 3. Water Level -> GPIO 33 (ADC)
water_pin = ADC(Pin(33))
water_pin.atten(ADC.ATTN_11DB)
water_pin.width(ADC.WIDTH_12BIT)

# 4. Rain Sensor -> GPIO 32 (ADC)
rain_pin = ADC(Pin(32))
rain_pin.atten(ADC.ATTN_11DB)
rain_pin.width(ADC.WIDTH_12BIT)

# 5. IR Sensor -> GPIO 25 (Digital Input)
ir_sensor = Pin(25, Pin.IN)

# 6. Actuators (Prepared for later use - currently idle)
servo_pin = Pin(13, Pin.OUT)
led_red = Pin(12, Pin.OUT)
led_green = Pin(14, Pin.OUT)

# ==========================================
# WIFI CONNECTION FUNCTION
# ==========================================
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(WIFI_SSID, WIFI_PASS)
        timeout = 0
        while not wlan.isconnected():
            time.sleep(1)
            timeout += 1
            if timeout > 15:
                print("WiFi connection timed out. Restarting...")
                machine.reset()
    print('WiFi Connected:', wlan.ifconfig())

# ==========================================
# MAIN LOOP
# ==========================================
connect_wifi()

print("System Initialized. Starting Main Loop...")

while True:
    try:
        # --- READ SENSORS ---
        
        # Read DHT22
        try:
            dht_sensor.measure()
            temp = dht_sensor.temperature()
            hum = dht_sensor.humidity()
        except OSError as e:
            print("Failed to read DHT sensor")
            temp = 0
            hum = 0

        # Read Analog Sensors (0-4095)
        ldr_val = ldr_pin.read()      
        water_val = water_pin.read()  
        rain_val = rain_pin.read()    
        
        # Read Digital IR
        ir_val = ir_sensor.value()    

        # --- DEBUG PRINT ---
        print("-" * 20)
        print(f"Temp: {temp}C, Hum: {hum}%")
        print(f"LDR: {ldr_val}, Water: {water_val}, Rain: {rain_val}")
        print(f"IR Status: {ir_val}")

        # --- SEND TO THINGSPEAK ---
        # Construct the URL
        request_url = (
            f"{THINGSPEAK_URL}?"
            f"api_key={THINGSPEAK_API_KEY}"
            f"&field1={temp}"
            f"&field2={hum}"
            f"&field3={ldr_val}"
            f"&field4={water_val}"
            f"&field5={rain_val}"
            f"&field6={ir_val}"
        )

        print("Sending data to ThingSpeak...")
        response = urequests.get(request_url)
        print(f"Server Response: {response.text}")
        response.close()

    except Exception as e:
        print(f"Error occurred: {e}")
    
    # --- DELAY ---
    print("Waiting 16 seconds...")
    time.sleep(16)