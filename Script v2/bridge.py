import paho.mqtt.client as mqtt
import json
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- CONFIGURATION ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "monash/studentB/tunnel_data"

# INFLUXDB SETTINGS
INFLUX_URL = "http://localhost:8086"
# PASTE YOUR LONG TOKEN BELOW
INFLUX_TOKEN = "tx2_FEOzI4qx-z4nSLiAFyLxwXyUmX4GBntWeTmcysrrB_LZEPlOB_uqI4y24bdVCPanTIj1a4iNQHcdpN7law==" 
INFLUX_ORG = "ShafwanCorporation"
INFLUX_BUCKET = "SmartTunnel"

# --- INFLUXDB CLIENT ---
client_db = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client_db.write_api(write_options=SYNCHRONOUS)

def on_connect(client, userdata, flags, rc):
    print("Bridge Connected to MQTT Broker!")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        # 1. Decode JSON
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        print(f"Received: {data}")

        # 2. Extract Data (Using the NEW names from ESP32)
        dist = float(data.get("ultrasonic_dist", 0))
        water = int(data.get("water_level", 0))
        rain = int(data.get("rain_value", 0))
        status = data.get("tunnel_status", "UNKNOWN")

        # 3. Create InfluxDB Point
        # We use 'tunnel_status' as a TAG so you can filter/color by it in Grafana
        point = Point("tunnel_metrics_v2") \
            .tag("status", status) \
            .field("distance_cm", dist) \
            .field("water_raw", water) \
            .field("rain_raw", rain)

        # 4. Save to Database
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        print(" -> Saved to InfluxDB")

    except Exception as e:
        print(f"Error processing data: {e}")

# --- START LISTENER ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, 1883, 60)
print("Bridge Listening... (Press Ctrl+C to stop)")
client.loop_forever()