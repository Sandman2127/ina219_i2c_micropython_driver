# use micropython

import time
from machine import I2C,Pin
import ssd1306
from micropython import const
from math import trunc
from INA219 import INA219
from fdrawer import FontDrawer

# set button pin to 16 and set internal pulldown
button_pin = const(16)
button = Pin(button_pin, Pin.IN, Pin.PULL_DOWN)
# calibration of current
mv_voltage_bus_resolution = const(4) # 4 mv
max_expected_amperage = 2.000 # 2 amps
current_lsb = max_expected_amperage/(2**15)  # 2 amps max yields 0.000061035 A or 61uV resolution
shunt_resistance = 0.1 # 100 mOhms
calibration_val = trunc((0.04096/(current_lsb * shunt_resistance))) # == 6710 max expected value used for calibration
# empicial correction to the calibration value
MeasShuntCurrent = 0.009007
INA219_Current = 0.0023
corrected_calibration_val = trunc((calibration_val * MeasShuntCurrent)/INA219_Current)

def rewrite_display(measurement,display_mode,prev_mode):
    # https://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html
    # overwrite the old stuff
    #display.fill_rect(x,y,w,h,c):
    
    dsp.fill_rect(10,10,128,64, 0)
    #if prev_mode == display_mode:
        # just fix the data area
    #    dsp.fill_rect(10,10,128,64, 0)
    #else:
        #dsp.fill_rect(10,10,128,64, 0)       # clear old measurement and draw a solid rectangle 10,10 to 117,53, colour=1 display.fill_rect(10, 10, 107, 43, 1) 
    if display_mode == 0:
        fd.print_str("V",106,22)
            
    elif display_mode == 1:
        fd.print_str("A",106,22)
        
    elif display_mode == 2:
        fd.print_str("W",106,22)
    
    elif display_mode == 3:
        fd.print_str("mV",100,22)
    
    fd.print_str(str(round(measurement,3)),24,22)
    dsp.show()

def check_display_mode(prev_mode,present_run_mode):
    # used to change the pointer mem address of the ina219 to collect the correct measurement
    if prev_mode == present_run_mode:
        pass
    elif present_run_mode == 0:
        ina.change_pointer_mem_address(ina.voltage_address)
    elif present_run_mode == 1:
        ina.change_pointer_mem_address(ina.shunt_voltage_address)
    elif present_run_mode == 2:
        pass
    elif present_run_mode == 3:
        ina.change_pointer_mem_address(ina.shunt_voltage_address)
    else:
        print("error in check_change_modes() function")
    

"""
                    *** MAIN ***
"""

# define setup variables

# screen
_sda = machine.Pin(0)
_scl = machine.Pin(1)
i2c_screen = I2C(0,sda=_sda,scl=_scl,freq=400000)
dsp = ssd1306.SSD1306_I2C(128, 64, i2c_screen)
dsp.fill(0)
fd = FontDrawer( frame_buffer=dsp,font_name='veram_m23')

# ina219
i2c_sensor = machine.I2C(0,sda=_sda,scl=_scl,freq=400000)    
devices = i2c_screen.scan()

# devices[1] == 64 is my i2c ina219
ina219_sensor_address = devices[1]
        
# setup ina219(i2c_sensor_interface <object> ,sensor_address <int>, current_lsb <float> , mv_voltage_bus_resolution <int>, corrected_calibration_val <int>)
ina = INA219(i2c_sensor,ina219_sensor_address,shunt_resistance,current_lsb,mv_voltage_bus_resolution,corrected_calibration_val) 

# measure and display loop
if len(devices) == 0:
     print("No i2c device !")
else:
     print('Found:',len(devices),'i2c devices')
     cnt = 0
     for dev in devices:
         print("Device:",cnt,dev,hex(dev))
         cnt += 1


display_mode = 0 # 0,1,2,3  > 3  --> reset to 0
# display_mode = 0 voltage
# display_mode = 1 current
# display_mode = 2 power
# display_mode = 3 shunt voltage

# change pointer mem address based on prev_mode
prev_mode = 99

while True:
    # setup display modes if button goes high
    if button.value() == 1:
        display_mode += 1
        if display_mode > 3:
            display_mode = 0

    # change memory pointer address to retrive correct measurement for voltage, current, power or shunt on display
    check_display_mode(prev_mode,display_mode)
    
    # voltage
    if display_mode == 0:
        ina.get_voltage()
        rewrite_display(ina.voltage,display_mode,prev_mode)
        prev_mode = 0
    # current
    elif display_mode == 1:
        ina.get_current()
        rewrite_display(ina.current,display_mode,prev_mode)
        prev_mode = 1
    # power
    elif display_mode == 2:
        ina.get_power()
        rewrite_display(ina.power,display_mode,prev_mode)
        prev_mode = 2
    # shunt voltage
    elif display_mode == 3:
        ina.get_shunt_voltage()
        rewrite_display(ina.shunt_voltage,display_mode,prev_mode)
        prev_mode = 3
    else:
        pass
    
    time.sleep_ms(100)
