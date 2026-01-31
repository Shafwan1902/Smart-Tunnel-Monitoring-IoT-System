import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- CONFIGURATION (YOU MUST EDIT THIS) ---
# 1. InfluxDB Settings (Get these from your Dashboard)
INFLUX_TOKEN = "bImZ8aDPYqzq_wKMpylXw4fRKZyGMenSf_I90y0fV6u1bzOf3fTdTA403ohX4Y2ZScHZhOZBewE2NwphDnwWAQ=="  # <--- PASTE YOUR TOKEN HERE!
INFLUX_ORG = "ShafwanCorporation"                   # Your Organization Name
INFLUX_BUCKET = "MiniProjectv1"             # Your Bucket Name
INFLUX_URL = "http://localhost:8086"

# 2. MQTT Settings (Must match Wokwi code)
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "shafwan19/sensor/data" 

# --- MAIN CODE (DO NOT EDIT BELOW) ---
# Connect to InfluxDB
print("Connecting to InfluxDB...", end="")
try:
    db_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = db_client.write_api(write_options=SYNCHRONOUS)
    print(" Success!")
except Exception as e:
    print(f" Failed to connect to DB: {e}")

# What happens when a message arrives from Wokwi?
def on_message(client, userdata, msg):
    try:
        # 1. Get the message
        raw_data = msg.payload.decode()
        print(f"Received: {raw_data}", end="")
        
        # 2. Convert text to a number
        value = float(raw_data)
        
        # 3. Save to InfluxDB
        point = Point("temperature").field("value", value)
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        print(" -> Saved to DB!")
        
    except Exception as e:
        print(f" -> Error: {e}")

# Start listening to MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.subscribe(MQTT_TOPIC)

print("Bridge is running... Waiting for data from Wokwi...")
mqtt_client.loop_forever()