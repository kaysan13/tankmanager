import time
import board
import adafruit_dht
from w1thermsensor import W1ThermSensor, Sensor

try:
    dhtSensor = adafruit_dht.DHT11(board.D4)
    DS18B20Sensor = W1ThermSensor(Sensor.DS18B20)
except Exception as error:
    raise error

while True:
    try:
        temperature_c = dhtSensor.temperature
        humidity = dhtSensor.humidity
        temperature = DS18B20Sensor.get_temperature()
        
        res = {
            "dht11": [{
                "temperature": "{:.1f}".format(temperature_c),
                "humidity": "{:.1f}".format(humidity)
            }],
            "DS18B20": "{:.1f}".format(temperature)
        }
        
        print(res)

    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        # print(error.args[0])
        time.sleep(2.0)
        continue
    except Exception as error:
        dhtSensor.exit()
        raise error

    time.sleep(10.0)
