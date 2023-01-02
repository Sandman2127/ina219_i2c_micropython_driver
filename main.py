# use micropython

import time
from machine import I2C,Pin
import ssd1306
from micropython import const
from math import trunc
from INA219 import INA219
import displayed
from fonts import bookerly_12,bookerly_15,ubuntu_condensed_12

# set button pin to 16 and set internal pulldown
button_pin = const(16)
button = Pin(button_pin, Pin.IN, Pin.PULL_DOWN)
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

def check_display_mode(prev_mode,present_run_mode):
    # used to change the pointer mem address of the ina219 to collect the correct measurement
    if prev_mode == present_run_mode:
        pass
    elif present_run_mode == 0 or present_run_mode == 99 :
        ina.change_pointer_mem_address(ina.voltage_address)
    elif present_run_mode == 1:
        ina.change_pointer_mem_address(ina.current_address)
    elif present_run_mode == 2:
        ina.change_pointer_mem_address(ina.power_address)
    else:
        print("error in check_change_modes() function")


"""
                    *** MAIN ***
"""

# define setup variables
orig_display = True
# screen
_sda = machine.Pin(0)
_scl = machine.Pin(1)
i2c_screen = I2C(0,sda=_sda,scl=_scl,freq=400000)
if orig_display:
    display = ssd1306.SSD1306_I2C(128, 64, i2c_screen)
    # write displays never changing functions 
    write_display_nonchanging_sections()
else: 
    dsp = displayed.SSD1306_12C(128, 32, i2c_screen)

# ina219
i2c_sensor = machine.I2C(0,sda=_sda,scl=_scl,freq=400000)    
devices = i2c_screen.scan()

# devices[1] == 64 is my i2c ina219
ina219_sensor_address = devices[1]
        
# setup ina219(i2c_sensor_interface <object> ,sensor_address <int>, current_lsb <float> , mv_voltage_bus_resolution <int>, corrected_calibration_val <int>)
ina = INA219(i2c_sensor,ina219_sensor_address,current_lsb,mv_voltage_bus_resolution,corrected_calibration_val) 

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
# display_mode = 3 shunt

# change pointer mem address based on prev_mode
prev_mode = 99

# draw data on screen
# mux.select_channel(0)
# mux.device.fill(0)
# mux.device.rect(85, 10, 32, 18, 1, False)
# mux.device.fw_text("inside", ubuntu_condensed_12, 89, 12)
# mux.device.text("T", 5, 8)
# mux.device.text(":", 21, 8)


while True:
    # setup display modes if button goes high
    if button.value() == 1:
        display_mode += 1
        if display_mode > 2:
            display_mode = 0
    # change memory pointer address to retrive correct measurement for voltage, current, power or shunt on display
    check_display_mode(prev_mode,display_mode)
    
    # voltage
    if display_mode == 0:
        ina.get_voltage()
        if orig_display:
            rewrite_display(ina.voltage,0,0)
        else:
            pass
        prev_mode = 0
        #print(ina.voltage)
        #print()

    # current
    elif display_mode == 1:
        ina.get_current()
        if orig_display:
            rewrite_display(0,ina.current,0)
        else:
            pass
        prev_mode = 1
        #print(ina.current)
        #print()
    
    # power
    elif display_mode == 2:
        ina.get_power()
        if orig_display:
            rewrite_display(0,0,ina.power)
        else:
            pass
        prev_mode = 2
        #print(ina.power)
        #print()
    # shunt voltage
    else:
        pass
        #ina.change_pointer_mem_address(ina.shunt_voltage_address)
        #ina.get_power()
        #print(ina.power)
    
    time.sleep_ms(75)
