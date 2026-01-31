from machine import Pin, ADC, time_pulse_us
from time import sleep_us, sleep

# --- 1. CONFIGURATION ---

# Output LEDs
red_led = Pin(23, Pin.OUT)
green_led = Pin(22, Pin.OUT)

# Rain Sensor (Pin 32)
# Usually: High Value = Dry, Low Value = Wet
rain_sensor = ADC(Pin(32))
rain_sensor.atten(ADC.ATTN_11DB) 

# Water Level Sensor (Pin 33)
# Usually: Low Value (0) = Dry, High Value (>1000) = Wet
water_contact_sensor = ADC(Pin(33))
water_contact_sensor.atten(ADC.ATTN_11DB)

# Ultrasonic Sensor (Pins 27, 14)
trig = Pin(27, Pin.OUT)
echo = Pin(14, Pin.IN)

# --- 2. THRESHOLDS (Adjust these numbers!) ---

# Ultrasonic: If distance is LESS than this (cm), water is too high.
ULTRASONIC_DANGER_CM = 15  

# Water Level (Pin 33): If value is HIGHER than this, road is flooded.
WATER_CONTACT_THRESHOLD = 1000 

# Rain (Pin 32): If value is LOWER than this, it is raining heavy.
RAIN_THRESHOLD = 2200

def get_ultrasonic_distance():
    trig.value(0)
    sleep_us(2)
    trig.value(1)
    sleep_us(10)
    trig.value(0)
    
    duration = time_pulse_us(echo, 1, 30000)
    
    if duration < 0:
        return 999 # Sensor error/Out of range
        
    # Calculate cm
    return (duration / 2) / 29.1

# --- 3. MAIN LOOP ---
print("Smart Tunnel Double-Sensor System Active...")

while True:
    # --- READ ALL SENSORS ---
    dist_cm = get_ultrasonic_distance()
    rain_val = rain_sensor.read()
    water_contact_val = water_contact_sensor.read()

    # --- CHECK DANGER CONDITIONS ---
    
    # 1. Check Ultrasonic (Ceiling Sensor)
    # Danger if water is closer than 15cm to the roof
    danger_ultrasonic = (dist_cm < ULTRASONIC_DANGER_CM)

    # 2. Check Water Level Sensor (Road Sensor)
    # Danger if sensor reading is high (water touching it)
    danger_contact = (water_contact_val > WATER_CONTACT_THRESHOLD)

    # 3. Check Rain
    # Danger if resistance drops (heavy rain)
    danger_rain = (rain_val < RAIN_THRESHOLD)

    # --- CONTROL LIGHTS ---
    # If ANY of the 3 conditions are true -> RED LIGHT
    if danger_ultrasonic or danger_contact or danger_rain:
        red_led.value(1)
        green_led.value(0)
        status = "DANGER"
    else:
        red_led.value(0)
        green_led.value(1)
        status = "SAFE"

    # --- DEBUGGING (Use this to fix your thresholds) ---
    print(f"STATUS: {status}")
    print(f" - Dist: {dist_cm:.1f}cm (Danger if < {ULTRASONIC_DANGER_CM})")
    print(f" - Water Level: {water_contact_val} (Danger if > {WATER_CONTACT_THRESHOLD})")
    print(f" - Rain: {rain_val} (Danger if < {RAIN_THRESHOLD})")
    print("-" * 30)
    
    sleep(1)