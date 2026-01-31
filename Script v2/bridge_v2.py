import paho.mqtt.client as mqtt
import json
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- 1. CONFIGURATION ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "monash/studentB/tunnel_data"

# InfluxDB Settings (Matched to your previous file)
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "tx2_FEOzI4qx-z4nSLiAFyLxwXyUmX4GBntWeTmcysrrB_LZEPlOB_uqI4y24bdVCPanTIj1a4iNQHcdpN7law=="
INFLUX_ORG = "ShafwanCorporation"
INFLUX_BUCKET = "SmartTunnel"

# --- 2. INFLUXDB SETUP ---
client_db = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client_db.write_api(write_options=SYNCHRONOUS)

# --- 3. MQTT CALLBACKS ---

def on_connect(client, userdata, flags, rc):
    print("Bridge Connected to MQTT Broker!")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        # A. Decode JSON from ESP32
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        
        # Debug: Print what we got
        print(f"Received: {data}")

        # B. Extract Numbers (Use .get(key, 0) to avoid crashing)
        # We removed 'tunnel_status', so we just grab the numbers now.
        dist = float(data.get("ultrasonic_dist", 0))
        water = int(data.get("water_level", 0))
        rain = int(data.get("rain_value", 0))

        # C. Prepare Data Point for Database
        # Measurement Name: "tunnel_metrics_final"
        point = Point("tunnel_metrics_final") \
            .field("distance_cm", dist) \
            .field("water_raw", water) \
            .field("rain_raw", rain)

        # D. Save to InfluxDB
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        print(" -> Saved to Database")

    except Exception as e:
        print(f"Error processing data: {e}")

# --- 4. START LISTENER ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("Bridge Starting...")
try:
    client.connect(MQTT_BROKER, 1883, 60)
    print("Listening for Sensor Data... (Press Ctrl+C to stop)")
    client.loop_forever()
except Exception as e:
    print(f"Could not connect to MQTT Broker: {e}")