from random import randint
from time import sleep

from machine import I2C, Pin

from tsl2591 import Gain, TSL2591, Time

"""
TSL2591 Sensor is connected to the Pi Pico on:
SDA = GP0
SCL = GP1
"""
device: I2C = I2C(0, scl=Pin(1), sda=Pin(0))
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
    print("*" * randint(1, 4))
    sleep(2)
