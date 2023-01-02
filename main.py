# use micropython

import time
from machine import I2C,Pin
import ssd1306
from micropython import const
from math import trunc
from INA219 import INA219

# calibration of current
mv_voltage_bus_resolution = const(4) # 4 mv
max_expected_amperage = 2.000 # 2 amps
current_lsb = max_expected_amperage/(2**15)  # 2 amps max yields 0.000061035 A or 610uA resolution
shunt_resistance = 0.1 # ohms
calibration_val = trunc((0.04096/(current_lsb * shunt_resistance))) # == 6710 max expected value used for calibration
# empicial correction to the calibration value
MeasShuntCurrent = 0.009007
INA219_Current = 0.0023
corrected_calibration_val = trunc((calibration_val * MeasShuntCurrent)/INA219_Current)

                            
def rewrite_display(voltage,current,power):
    # https://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html
    # overwrite the old stuff
    #display.fill_rect(x,y,w,h,c):
    display.fill_rect(70, 0, 58, 12, 0)
    display.fill_rect(70, 24, 58, 12, 0)
    display.fill_rect(70, 48, 58, 12, 0)
    # write the new stuff
    display.text(str(round(power,3)),70,0,1)
    display.text(str(round(voltage,3)),70,24,1)
    display.text(str(round(current,3)),70,48,1)
    display.show()
    output = [power,voltage,current]
    return output

def write_display_nonchanging_sections():
    header = ""
    display.fill(0)
    display.text('Power:', 5, 0, 1)
    display.text('Voltage:', 5, 24, 1)
    display.text('Current:', 5, 48, 1)
    display.show()

"""
                    *** MAIN ***
"""

# define setup variables
debug = 0 
# perform setup of globals
# screen
sda_screen = machine.Pin(0)
scl_screen = machine.Pin(1)
i2c_screen = I2C(0,sda=sda_screen,scl=scl_screen,freq=400000)
display = ssd1306.SSD1306_I2C(128, 64, i2c_screen)

# ina219
sda_sensor = machine.Pin(0)
scl_sensor = machine.Pin(1)
i2c_sensor = machine.I2C(0,sda=sda_sensor,scl=scl_sensor,freq=400000)    
devices = i2c_screen.scan()

# devices[1] == 64 is my i2c ina219
ina219_sensor_address = devices[1]
        
# setup ina219(i2c_sensor_interface,mv_voltage_bus_resolution
ina = INA219(i2c_sensor,ina219_sensor_address,current_lsb,mv_voltage_bus_resolution,corrected_calibration_val) # 2nd i2c device in my case .e. the ina219
    
# write displays never changing functions 
write_display_nonchanging_sections()

# measure and display loop
if len(devices) == 0:
     print("No i2c device !")
else:
     print('found:',len(devices),'i2c devices')
     cnt = 0
     for dev in devices:
         print("device:",cnt,dev,hex(dev))
         cnt += 1

# set button pin to 16 and set internal pulldown
button = Pin(16, Pin.IN, Pin.PULL_DOWN)

display_mode = 0 # 0,1,2,3  > 3  --> reset to 0
# display_mode = 0 voltage
# display_mode = 1 current
# display_mode = 2 power
# display_mode = 3 shunt

# change pointer mem address based on prev_mode
prev_mode = 99
while True:
    # setup display modes
    if button.value() == 1:
        display_mode += 1
        if display_mode > 2:
            display_mode = 0
    # voltage
    if display_mode == 0:
        if prev_mode == 0:
            pass
        else:
            ina.change_pointer_mem_address(ina.voltage_address)
        ina.get_voltage()
        rewrite_display(ina.voltage,0,0)
        prev_mode = 0
        #print(ina.voltage)
        #print()

    # current
    elif display_mode == 1:
        if prev_mode == 1:
            pass
        else:
            ina.change_pointer_mem_address(ina.current_address)
            #ina.change_pointer_mem_address(shunt_voltage_address)
        ina.get_current()
        rewrite_display(0,ina.current,0)
        prev_mode = 1
        #print(ina.current)
        #print()
    
    # power
    elif display_mode == 2:
        if prev_mode == 2:
            pass
        else:
            ina.change_pointer_mem_address(ina.power_address)
        ina.get_power()
        rewrite_display(0,0,ina.power)
        prev_mode = 2
        #print(ina.power)
        #print()

    # shunt voltage
    else:
        ina.change_pointer_mem_address(shunt_voltage_address)
        ina.get_power()
        #print(ina.power)
        #print()
    time.sleep_ms(75)
