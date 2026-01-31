import paho.mqtt.client as mqtt
import json # <--- Need this to unpack the box
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- 1. CONFIGURATION ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "monash/studentB/tunnel_data"

# InfluxDB Settings
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "YOUR_INFLUX_TOKEN"
INFLUX_ORG = "YOUR_INFLUX_ORG"
INFLUX_BUCKET = "YOUR_INFLUX_BUCKET"

# --- INFLUXDB SETUP ---
client_db = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client_db.write_api(write_options=SYNCHRONOUS)

# --- CALLBACKS ---
def on_connect(client, userdata, flags, rc):
    print("Bridge Connected to MQTT Broker!")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        # 1. Decode the JSON message
        payload_str = msg.payload.decode()
        data = json.loads(payload_str)
        print(f" Received: {data}")

        # 2. Create the Data Point (Saving ALL sensors at once)
        point = Point("tunnel_metrics") \
            .field("temperature", float(data["temperature"])) \
            .field("humidity", float(data["humidity"])) \
            .field("light", float(data["light_intensity"])) \
            .field("water", float(data["water_level"])) \
            .field("rain", float(data["rain_intensity"])) \
            .field("car", int(data["car_detected"]))

        # 3. Save to InfluxDB
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        print(" -> Data saved to DB")

    except Exception as e:
        print(f"Error processing message: {e}")

# --- START BRIDGE ---
client_mqtt = mqtt.Client()
client_mqtt.on_connect = on_connect
client_mqtt.on_message = on_message

client_mqtt.connect(MQTT_BROKER, 1883, 60)
print("Bridge Started... Waiting for ESP32 data...")
client_mqtt.loop_forever()
