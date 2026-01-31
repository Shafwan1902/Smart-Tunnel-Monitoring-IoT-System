import paho.mqtt.client as mqtt
import json
import time
import requests  # <--- NEW LIBRARY for Telegram
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- 1. CONFIGURATION ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "monash/studentB/tunnel_data"

# InfluxDB Settings
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "tx2_FEOzI4qx-z4nSLiAFyLxwXyUmX4GBntWeTmcysrrB_LZEPlOB_uqI4y24bdVCPanTIj1a4iNQHcdpN7law=="
INFLUX_ORG = "ShafwanCorporation"
INFLUX_BUCKET = "SmartTunnel"

# --- TELEGRAM CONFIGURATION ---
# PASTE YOUR BOT TOKEN INSIDE THE QUOTES BELOW:
BOT_TOKEN = "8475604135:AAF1BMQi0Xckrik1BRtFHXyVBwtO3mNM3qM" 

# I found this Chat ID in your screenshot:
CHAT_ID = "-1003275623160"

# How many seconds to wait between alerts (to prevent spamming)
ALERT_COOLDOWN = 10  
last_alert_time = 0  

# --- 2. INFLUXDB SETUP ---
client_db = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client_db.write_api(write_options=SYNCHRONOUS)

# --- 3. HELPER FUNCTION: SEND TELEGRAM ---
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload)
        # CHANGED THIS LINE: Do not print the 'message' variable (which has emojis)
        print(" Telegram Alert Sent Successfully! (Check your phone)") 
    except Exception as e:
        print(f" Telegram Error: {e}")

# --- 4. MQTT CALLBACKS ---

def on_connect(client, userdata, flags, rc):
    print("Bridge Connected to MQTT Broker!")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global last_alert_time
    
    try:
        # A. Decode JSON
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        print(f"Received: {data}")

        # B. Extract Data
        dist = float(data.get("ultrasonic_dist", 999))
        water = int(data.get("water_level", 0))
        rain = int(data.get("rain_value", 4095))
        r_led = int(data.get("led_red", 0))
        g_led = int(data.get("led_green", 0))

        # --- C. REAL-TIME SAFETY CHECK ---
        current_time = time.time()
        
        # Only check if cooldown has passed
        if (current_time - last_alert_time) > ALERT_COOLDOWN:
            alert_msg = ""
            
            # Rule 1: Water Level Flood
            if water > 1000:
                alert_msg = f" <b>Tunnel Full!</b>\nWater Level is {water}. Evacuate Tunnel."
            
            # Rule 2: Ultrasonic Tunnel Full
            elif dist < 10:
                alert_msg = f" <b>Flood Critical!</b>\nWater is {dist}cm from ceiling."
            
            # Rule 3: Heavy Storm
            elif rain < 3000:
                alert_msg = f" <b>STORM ALERT!</b>\nHeavy Rain Detected (Sensor: {rain})."

            # If danger found, send message
            if alert_msg != "":
                send_telegram_alert(alert_msg)
                last_alert_time = current_time  # Reset timer

        # --- D. SAVE TO INFLUXDB ---
        point = Point("tunnel_metrics_final") \
            .field("distance_cm", dist) \
            .field("water_raw", water) \
            .field("rain_raw", rain) \
            .field("is_danger_on", r_led) \
            .field("is_safe_on", g_led)

        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        print(" -> Saved to Database")

    except Exception as e:
        print(f"Error processing data: {e}")

# --- 5. START LISTENER ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("Bridge Starting...")
print("1. Connecting to MQTT...")
try:
    client.connect(MQTT_BROKER, 1883, 60)
    print("2. Listening for Sensor Data... (Press Ctrl+C to stop)")
    client.loop_forever()
except Exception as e:
    print(f"Could not connect to MQTT Broker: {e}")