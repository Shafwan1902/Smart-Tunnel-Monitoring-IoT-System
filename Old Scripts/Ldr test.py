from machine import Pin, ADC
import time

# Set up the Analog Pin on GPIO 34
# ADC1 is best for sensors (pins 32-39)
ldr = ADC(Pin(34))

# Set attenuation to read the full 0-3.3V range
# Without this, it maxes out at 1V
ldr.atten(ADC.ATTN_11DB)

print("Reading LDR Module (Analog)...")

while True:
    try:
        # Read a value between 0 (0V) and 4095 (3.3V)
        light_value = ldr.read()
        
        print(f"Light Level: {light_value}")
        
        # Simple Logic to help you visualize
        if light_value < 1000:
             print(" -> It is DARK")
        elif light_value > 3000:
             print(" -> It is BRIGHT")
             
    except Exception as e:
        print("Error reading LDR")
        
    time.sleep(0.5)