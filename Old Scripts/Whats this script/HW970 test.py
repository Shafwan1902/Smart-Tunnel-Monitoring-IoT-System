from machine import Pin, ADC
from time import sleep

# Initialize the sensor on GPIO 35
# We use Pin 35 because your Pin 34 is busy with the LDR
sensor_pin = ADC(Pin(35))

# IMPORTANT: Set attenuation to allow reading up to 3.3V
# Without this, the ESP32 ADC maxes out at ~1.1V
sensor_pin.atten(ADC.ATTN_11DB)

# Optional: Set resolution to 12-bit (0-4095)
# (This is usually the default for ESP32 in MicroPython)
sensor_pin.width(ADC.WIDTH_12BIT)

print("Starting HW-870 Sensor Test on Pin 35...")

while True:
    # Read raw value (0 to 4095)
    raw_value = sensor_pin.read()
    
    # Calculate approximate voltage
    voltage = raw_value * (3.3 / 4095)
    
    print("Raw Value:", raw_value, "| Voltage:", round(voltage, 2), "V")
    
    # Simple logic for IR reflection
    # Adjust '200' and '3000' based on what you see in the shell
    if raw_value < 500:
        print(" -> Status: Close/Reflective")
    else:
        print(" -> Status: Far/Dark")
        
    sleep(0.5)