# https://www.rototron.info/dht22-tutorial-for-raspberry-pi/

import pigpio
from time import sleep
# this connects to the pigpio daemon which must be started first
pi = pigpio.pi()
# Pigpio DHT22 module should be in same folder as your program
import DHT22
s = DHT22.sensor(pi, 4)
s.trigger()
sleep(.03) # Necessary on faster Raspberry Pi's
print('{:3.2f}'.format(s.humidity() / 1.))
print('{:3.2f}'.format(s.temperature() / 1.))
s.cancel()
pi.stop()

# TODO: create a DHT22 sensor and inject in Sensor (olso for client)