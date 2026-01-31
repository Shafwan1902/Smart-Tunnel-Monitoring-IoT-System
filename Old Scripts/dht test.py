import dht
from machine import Pin
import time

# We use Pin(27) because we are listening for digital pulses
# We do NOT use ADC()
sensor = dht.DHT22(Pin(27))

print("Reading DHT22 Module...")

while True:
    try:
        # 1. Ask sensor to send data
        sensor.measure()
        
        # 2. Read the results
        t = sensor.temperature()
        h = sensor.humidity()
        
        print(f"Temp: {t}°C  |  Humidity: {h}%")
        
    except OSError as e:
        print("Error: Sensor not responding.")
        print("Check: Is the signal wire on GPIO 27?")
        
    time.sleep(2)