# use circuit python

import time
import machine
from ina219 import INA219  # micropython version: https://github.com/chrisb2/pyb_ina219

# circuit python version
# sudo pip3 install adafruit-circuitpython-ina219
# import board
# import busio 
# import adafruit_ina219  


# general i2c stuff 
# print('Scan i2c bus...')
# devices = i2c.scan()

# ina219
# sda_sensor = machine.Pin(16)
# scl_sensor = machine.Pin(17)
# i2c = machine.I2C(1,sda=sda_sensor,scl=scl_sensor,freq=400000)

# if len(devices) == 0:
# print("No i2c device !")
# else:
# print('i2c devices found:',len(devices))

# for device in devices:
# print("Decimal address: ",device," | Hexa address: ",hex(device))




# perform setup of globals
# screen
sda_screen = machine.Pin(1)
scl_screen = machine.Pin(2)
i2c_screen = machine.I2C(0,sda=sda_screen,scl=scl_screen,freq=400000)
display = ssd1306.SSD1306_I2C(128, 64, i2c_screen)

# ina219
sda_sensor = machine.Pin(16)
scl_sensor = machine.Pin(17)
i2c_sensor = machine.I2C(1,sda=sda_sensor,scl=scl_sensor,freq=400000)

# i2c_bus = board.I2C()  # uses board.SCL and board.SDA
# i2c_bus = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller

# ina219 = adafruit_ina219.INA219(i2c)
# print("ina219 test")
# display some of the advanced field (just to test)
# print("Config register:")
# print("  bus_voltage_range:    0x%1X" % ina219.bus_voltage_range)
# print("  gain:                 0x%1X" % ina219.gain)
# print("  bus_adc_resolution:   0x%1X" % ina219.bus_adc_resolution)
# print("  shunt_adc_resolution: 0x%1X" % ina219.shunt_adc_resolution)
# print("  mode:                 0x%1X" % ina219.mode)
# print("")

# optional : change configuration to use 32 samples averaging for both bus voltage and shunt voltage
# ina219.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
# ina219.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
# optional : change voltage range to 16V
# ina219.bus_voltage_range = BusVoltageRange.RANGE_16V




def rewrite_display(voltage,current,power):
    #https://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html
    display.txt(str(round(voltage,4)),20,0,1)
    display.txt(str(round(current,4)),15,24,1)
    display.txt(str(round(power,4)),10,48,1)
    display.show()


def write_display_nonchanging_sections():
    header = ""
    display.fill(0)
    display.fill_rect(0, 0, 32, 32, 1)
    display.fill_rect(2, 2, 28, 28, 0)
    display.vline(9, 8, 22, 1)
    display.vline(16, 2, 22, 1)
    display.vline(23, 8, 22, 1)
    display.fill_rect(26, 24, 2, 4, 1)
    display.text('MicroPython', 40, 0, 1)
    display.text('SSD1306', 40, 12, 1)
    display.text('OLED 128x64', 40, 24, 1)
    display.show()


# setup ina219 
#I2C_INTERFACE_NO = 2
SHUNT_OHMS = 0.1  # Check value of shunt used with your INA219
# I think this is 
ina = INA219(SHUNT_OHMS,i2c_sensor)
#I2C_INTERFACE_NO = 2
#ina = INA219(SHUNT_OHMS,I2C(I2C_INTERFACE_NO))
ina.configure()
# write displays never changing functions 
write_display_nonchanging_sections()
# measure and display loop
while True:
    ### for the micropython  ### 
    # print("Bus Voltage: %.3f V" % ina.voltage())
    # print("Current: %.3f mA" % ina.current())
    # print("Power: %.3f mW" % ina.power())

    # Check internal calculations haven't overflowed (doesn't detect ADC overflows)
    if not ina.voltage:
        print("Internal Overflow Detected!")
        print("")
    else:
        rewrite_display(ina.voltage(),ina.current(),ina.power())
    # time.sleep(1)
    time.sleep_ms(100)


    ### for circuit python ### 
    # bus_voltage = ina219.bus_voltage  # voltage on V- (load side)
    # shunt_voltage = ina219.shunt_voltage  # voltage between V+ and V- across the shunt
    # current = ina219.current  # current in mA
    # power = ina219.power  # power in watts

    # print("Bus Voltage: %.3f V" % ina.voltage())
    # print("Current: %.3f mA" % ina.current())
    # print("Power: %.3f mW" % ina.power())

    # INA219 measure bus voltage on the load side. So PSU voltage = bus_voltage + shunt_voltage
    # print("Voltage (VIN+) : {:6.3f}   V".format(bus_voltage + shunt_voltage))
    # print("Voltage (VIN-) : {:6.3f}   V".format(bus_voltage))
    # print("Shunt Voltage  : {:8.5f} V".format(shunt_voltage))
    # print("Shunt Current  : {:7.4f}  A".format(current / 1000))
    # print("Power Calc.    : {:8.5f} W".format(bus_voltage * (current / 1000)))
    # print("Power Register : {:6.3f}   W".format(power))
    # print("")
    # if not ina219.overflow:
    #     print("Internal Overflow Detected!")
    #     print("")
    # else:
    #     write_display(bus_voltage + shunt_voltage,current,power)

    # time.sleep(1)
    #time.sleep_ms(100)
