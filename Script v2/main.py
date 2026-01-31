import time
import ujson
from machine import Pin, ADC, time_pulse_us
import network
from umqttsimple import MQTTClient

# --- CONFIGURATION ---
WIFI_SSID = "iPhone"         # <--- CHANGE THIS
WIFI_PASSWORD = "12345678"   # <--- CHANGE THIS

MQTT_BROKER = "broker.hivemq.com"
MQTT_CLIENT_ID = "MySmartTunnel_NewHardware"
MQTT_TOPIC = "monash/studentB/tunnel_data"

# --- HARDWARE SETUP ---
# LEDs
red_led = Pin(23, Pin.OUT)
green_led = Pin(22, Pin.OUT)

# Rain Sensor (Pin 32)
rain_sensor = ADC(Pin(32))
rain_sensor.atten(ADC.ATTN_11DB) 

# Water Level Sensor (Pin 33)
water_sensor = ADC(Pin(33))
water_sensor.atten(ADC.ATTN_11DB)

# Ultrasonic Sensor (Trig 27, Echo 14)
trig = Pin(27, Pin.OUT)
echo = Pin(14, Pin.IN)

# --- THRESHOLDS ---
ULTRASONIC_DANGER_CM = 15  
WATER_CONTACT_THRESHOLD = 1000 
RAIN_THRESHOLD = 2200

# --- HELPER FUNCTIONS ---
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to WiFi...', end="")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            print(".", end="")
            time.sleep(0.5)
    print('\nWiFi Connected!')

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

# --- MAIN SETUP ---
connect_wifi()
print("Connecting to MQTT...", end="")
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
try:
    client.connect()
    print(" Connected!")
except:
    print(" MQTT Connection Failed (Will try loop anyway)")

print("Smart Tunnel System Active...")

# --- MAIN LOOP ---
while True:
    try:
        # 1. READ SENSORS
        dist_cm = get_ultrasonic_distance()
        rain_val = rain_sensor.read()
        water_val = water_sensor.read()

        # 2. SAFETY LOGIC (HARDWARE ONLY)
        # This part controls the LEDs but we won't send the result to the cloud
        danger_ultrasonic = (dist_cm < ULTRASONIC_DANGER_CM)
        danger_contact = (water_val > WATER_CONTACT_THRESHOLD)
        danger_rain = (rain_val < RAIN_THRESHOLD)

        if danger_ultrasonic or danger_contact or danger_rain:
            red_led.value(1)
            green_led.value(0)
            status_print = "DANGER" # Just for your black screen, not for cloud
        else:
            red_led.value(0)
            green_led.value(1)
            status_print = "SAFE"

        # 3. PREPARE JSON DATA
        # REMOVED "tunnel_status" so Grafana only gets pure numbers
        payload = {
            "ultrasonic_dist": dist_cm,
            "water_level": water_val,
            "rain_value": rain_val
        }
        
        # 4. SEND TO BRIDGE
        msg_str = ujson.dumps(payload)
        client.publish(MQTT_TOPIC, msg_str)
        print(f"Sent: {status_print} | Dist: {dist_cm:.1f}cm | Water: {water_val}")

    except Exception as e:
        print("Error:", e)

    time.sleep(1)