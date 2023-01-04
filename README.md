# Simple Voltage and Amperage display of ina219 i2c module w/ssd1306 128x64 screen

### requires only micropython 1.19.1 and the base builtin machine function

### vital imports:
```
import time
from machine import I2C,Pin
import ssd1306
from micropython import const
from math import trunc
```

### user configuration:

1. upload INA219.py to the lib location: /lib/INA219.py on the pico
2. configure the button PIN (default: GP16) 
3. enter the mv_voltage bus resolution if different from the default (4 mV)
4. enter the max expected amperage (default 2.0)


### code to configure in main.py if you want to display the results on an ssd1306 128x64 screen
```
button_pin = const(16)                #   <int> any GPIO pin on the rpico, the pin is kept low through a 100kΩ resistor and pulsed high to change display modes
...
mv_voltage_bus_resolution = const(4)  #   <int> change if different from 4 mV
max_expected_amperage = 2.0           #   <float> from 0.0 <--> 3.2 with the default 2.0

```


