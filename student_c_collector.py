import paho.mqtt.client as mqtt
import json
import csv
import time
from datetime import datetime

# --- CONFIGURATION ---
BROKER = "broker.hivemq.com"
TOPIC = "monash/studentB/tunnel_data"
FILENAME = "tunnel_analytics_data.csv"

# Create the CSV file with ALL headers
try:
    with open(FILENAME, 'x', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Water Level", "Rain", "Light", "Temperature", "Humidity", "Car Detected"])
except FileExistsError:
    pass

def on_message(client, userdata, msg):
    try:
        # 1. Decode the JSON data
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        
        # 2. Add a timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 3. DEBUG: Print what we found so you can be sure
        print(f"[{timestamp}] Received: {data}")
        
        # 4. GET DATA using the EXACT names from your main.py
        water = data.get("water_level", 0)
        rain  = data.get("rain_intensity", 0)      # <--- Fixed Name
        light = data.get("light_intensity", 0)     # <--- Fixed Name
        temp  = data.get("temperature", 0)
        hum   = data.get("humidity", 0)
        car   = data.get("car_detected", 0)

        # 5. Save to CSV file
        with open(FILENAME, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, water, rain, light, temp, hum, car])
            
    except Exception as e:
        print("Error saving data:", e)

# Setup MQTT Client
client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, 1883, 60)
client.subscribe(TOPIC)

print(f"Listening for data on {TOPIC}...")
print(f"Saving to {FILENAME} (Press Ctrl+C to stop)")
client.loop_forever()