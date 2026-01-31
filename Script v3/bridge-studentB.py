import paho.mqtt.client as mqtt
import json
import time
import requests
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# ==========================================
#  1. CONFIGURATION SECTION
# ==========================================

# --- MQTT SETTINGS ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "monash/studentB/tunnel_data"

# --- INFLUXDB SETTINGS ---
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "tx2_FEOzI4qx-z4nSLiAFyLxwXyUmX4GBntWeTmcysrrB_LZEPlOB_uqI4y24bdVCPanTIj1a4iNQHcdpN7law=="
INFLUX_ORG = "ShafwanCorporation"
INFLUX_BUCKET = "SmartTunnel"

# --- TELEGRAM SETTINGS ---
#  PASTE YOUR REAL TOKEN BELOW:
BOT_TOKEN = "8475604135:AAF1BMQi0Xckrik1BRtFHXyVBwtO3mNM3qM"
CHAT_ID = "-1003275623160"

# --- SAFETY SETTINGS ---
ALERT_COOLDOWN = 10   
last_alert_time = 0   

# ==========================================
#  2. SETUP & HELPER FUNCTIONS
# ==========================================

client_db = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client_db.write_api(write_options=SYNCHRONOUS)

def send_telegram_alert_measured(message_text, sensor_time):
    """
    Calculates the total time from Sensor Receive -> Telegram Sent
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message_text,
        "parse_mode": "HTML"
    }

    try:
        # Perform the request
        requests.post(url, data=payload)
        
        # ⏱ Stop Clock (Message Sent)
        send_time = time.time()
        
        # Calculate Latency
        total_latency = send_time - sensor_time
        
        # Format times for display (HH:MM:SS.ms)
        t_in = datetime.fromtimestamp(sensor_time).strftime('%H:%M:%S.%f')[:-3]
        t_out = datetime.fromtimestamp(send_time).strftime('%H:%M:%S.%f')[:-3]

        print("------------------------------------------------")
        print(f" >> [TIMING] Sensor Recv: {t_in}")
        print(f" >> [TIMING] Telegram Sent: {t_out}")
        print(f" >>  TOTAL LATENCY: {total_latency:.4f} seconds")
        print("------------------------------------------------")
            
    except Exception as e:
        print(f" >> [TELEGRAM] Error: {e}")

# ==========================================
#  3. MQTT LOGIC
# ==========================================

def on_connect(client, userdata, flags, rc):
    print("---------------------------------------")
    print(f" Bridge Connected to {MQTT_BROKER}")
    print(f" Listening to topic: {MQTT_TOPIC}")
    print("---------------------------------------")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global last_alert_time
    
    # ⏱ Start Clock (Data Arrives)
    sensor_receive_time = time.time()
    
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        
        dist = float(data.get("ultrasonic_dist", 999))
        water = int(data.get("water_level", 0))
        rain = int(data.get("rain_value", 4095))
        r_led = int(data.get("led_red", 0))
        g_led = int(data.get("led_green", 0))

        # print(f" Data: Water={water} | Dist={dist:.1f}cm") # Optional: Un-comment to see stream

        # --- REAL-TIME SAFETY CHECK ---
        # Only check if cooldown has passed
        if (sensor_receive_time - last_alert_time) > ALERT_COOLDOWN:
            alert_msg = ""
            
            if water > 1000:
                alert_msg = f" <b>FLOOD CRITICAL!</b>\nWater Level is {water}."
            elif dist < 10:
                alert_msg = f" <b>TUNNEL FULL!</b>\nWater is {dist:.1f}cm from ceiling."
            elif rain < 3000:
                alert_msg = f" <b>STORM ALERT!</b>\nHeavy Rain Detected ({rain})."

            if alert_msg != "":
                # Pass the 'sensor_receive_time' to the function to calculate the full duration
                send_telegram_alert_measured(alert_msg, sensor_receive_time)
                last_alert_time = sensor_receive_time

        # Save to InfluxDB
        point = Point("tunnel_metrics_final") \
            .field("distance_cm", dist) \
            .field("water_raw", water) \
            .field("rain_raw", rain) \
            .field("is_danger_on", r_led) \
            .field("is_safe_on", g_led)

        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

    except Exception as e:
        print(f" Error: {e}")

# ==========================================
#  4. MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, 1883, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n Bridge Stopped.")