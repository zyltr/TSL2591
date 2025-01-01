# TSL 2591

This class provides an interface for interacting with the TSL2591 light sensor via I2C communication.
It supports configuring the sensor, reading luminosity data, and calculating light intensity in lux.

```python
from machine import I2C, Pin
from time import sleep

from tsl2591 import Gain, TSL2591, Time

"""
TSL2591 Sensor is connected to the Pi Pico on:
SDA = GP2
SCL = GP3
"""
device: I2C = I2C(1, scl=Pin(3), sda=Pin(2))
sensor: TSL2591 = TSL2591(device=device)

"""
Configure TSL2591 Sensor
"""
sensor.gain = Gain.MEDIUM
sensor.time = Time.MS300

"""
Readings
"""
while True:
    print(f"Full Spectrum: {sensor.full_spectrum}")
    print(f"Infrared: {sensor.infrared}")
    print(f"Lux: {sensor.lux}")
    print(f"Raw Luminosity: {sensor.raw_luminosity}")
    print(f"Visible: {sensor.visible}")
    print()
    sleep(4)
```
