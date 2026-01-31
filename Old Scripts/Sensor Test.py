import dht
from machine import Pin, ADC
import time

# ==================================================
# 1. SENSOR SETUP
# ==================================================

# A. DHT22 (Temperature & Humidity) - GPIO 21
d_sensor = dht.DHT22(Pin(21))

# B. LDR (Light Intensity) - GPIO 34 (ADC)
ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)  # 0 - 3.3V range

# C. Water Level Sensor - GPIO 33 (ADC)
water_sensor = ADC(Pin(33))
water_sensor.atten(ADC.ATTN_11DB)

# D. Rain Sensor - GPIO 32 (ADC)
rain_sensor = ADC(Pin(32))
rain_sensor.atten(ADC.ATTN_11DB)

# E. IR Sensor (Object Detection) - GPIO 25 (DIGITAL)
ir_sensor = Pin(25, Pin.IN)

print("Smart Tunnel Monitoring System")
print("System started...")
print("=" * 50)

# ==================================================
# 2. MAIN LOOP
# ==================================================
while True:
    try:
        # -------- READ SENSORS --------
        # 1. DHT22
        d_sensor.measure()
        temp = d_sensor.temperature()
        hum = d_sensor.humidity()

        # 2. Analog Sensors (0 - 4095)
        light_raw = ldr.read()
        water_raw = water_sensor.read()
        rain_raw = rain_sensor.read()

        # 3. IR Sensor (0 = Object detected, 1 = Clear)
        ir_status = ir_sensor.value()

        # -------- VOLTAGE CALCULATION (OPTIONAL) --------
        v_light = (light_raw / 4095) * 3.3
        v_water = (water_raw / 4095) * 3.3
        v_rain = (rain_raw / 4095) * 3.3

        # -------- DISPLAY DATA --------
        print(f"TEMPERATURE : {temp:.1f} °C | HUMIDITY : {hum:.1f} %")
        print(f"LDR         : {light_raw:<5} ({v_light:.2f} V)")
        print(f"WATER LEVEL : {water_raw:<5} ({v_water:.2f} V)")
        print(f"RAIN SENSOR : {rain_raw:<5} ({v_rain:.2f} V)")

        if ir_status == 0:
            print("IR SENSOR   : Object Detected")
        else:
            print("IR SENSOR   : Clear")

        # -------- TUNNEL LOGIC (EXAMPLE) --------
        tunnel_status = "OPEN (Normal)"

        # Example conditions (adjust threshold after calibration)
        if rain_raw < 1500 or water_raw > 2000 or ir_status == 0:
            tunnel_status = "CLOSED (Hazard Detected!)"

        print(f">>> TUNNEL STATUS: {tunnel_status}")
        print("-" * 50)

    except OSError:
        print("DHT22 reading error. Check wiring.")
    except Exception as e:
        print("Unexpected error:", e)

    time.sleep(2)