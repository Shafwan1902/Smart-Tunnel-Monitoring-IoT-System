# main.py - Smart Tunnel MONITORING ONLY
import time
import ujson
import dht
from machine import Pin, ADC
from umqttsimple import MQTTClient

# --- WI-FI CONFIGURATION (CHANGE THESE!) ---
WIFI_SSID = "iPhone"
WIFI_PASSWORD = "12345678"

# --- MQTT CONFIGURATION ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_CLIENT_ID = "MySmartTunnel_ESP32"
MQTT_TOPIC = "monash/studentB/tunnel_data"

# --- SENSOR PINS (Based on your list) ---
d_sensor = dht.DHT22(Pin(21))

ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB) 

water_sensor = ADC(Pin(33)) # Red Brick Sensor
water_sensor.atten(ADC.ATTN_11DB)

rain_sensor = ADC(Pin(32))
rain_sensor.atten(ADC.ATTN_11DB)

ir_sensor = Pin(25, Pin.IN)

# --- CONNECT TO WIFI ---
import network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)
print("Connecting to WiFi...", end="")
while not wlan.isconnected():
    time.sleep(0.5)
    print(".", end="")
print(" Connected!")

# --- CONNECT TO MQTT ---
print("Connecting to MQTT...", end="")
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
client.connect()
print(" Connected!")

# --- MAIN LOOP ---
while True:
    try:
        # 1. Read Sensors
        d_sensor.measure()
        temp = d_sensor.temperature()
        hum = d_sensor.humidity()
        
        light_val = ldr.read()
        water_val = water_sensor.read()
        rain_val = rain_sensor.read()
        ir_status = ir_sensor.value() # 0=Object, 1=Clear

        # 2. Package into JSON
        # We send EVERYTHING in one box
        payload = {
            "temperature": temp,
            "humidity": hum,
            "light_intensity": light_val,
            "water_level": water_val,
            "rain_intensity": rain_val,
            "car_detected": 1 if ir_status == 0 else 0 
        }
        
        # 3. Send to Laptop (Bridge)
        msg_str = ujson.dumps(payload)
        print(f"Sending: {msg_str}")
        client.publish(MQTT_TOPIC, msg_str)
        
    except OSError:
        print("Sensor Error (DHT usually)")
    except Exception as e:
        print("Error:", e)
        # Optional: Reconnect logic here if needed

    time.sleep(2) # Send every 2 seconds