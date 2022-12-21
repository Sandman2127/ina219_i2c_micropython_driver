# use micropython

import time
import machine
import ssd1306
#from ina219 import INA219  # micropython version: https://github.com/chrisb2/pyb_ina219

# general i2c stuff 
# print('Scan i2c bus...')
# devices = i2c.scan()

# if len(devices) == 0:
# print("No i2c device !")
# else:
# print('i2c devices found:',len(devices))

# for device in devices:
# print("Decimal address: ",device," | Hexa address: ",hex(device))


# perform setup of globals
# screen
sda_screen = machine.Pin(0)
scl_screen = machine.Pin(1)
i2c_screen = machine.I2C(0,sda=sda_screen,scl=scl_screen,freq=400000)
display = ssd1306.SSD1306_I2C(128, 64, i2c_screen)

# ina219
sda_sensor = machine.Pin(16)
scl_sensor = machine.Pin(17)
i2c_sensor = machine.I2C(1,sda=sda_sensor,scl=scl_sensor,freq=400000)

def rewrite_display(voltage,current,power,prev_data):
    #https://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html
    # overwrite the old stuff
    prev_power,prev_voltage,prev_current = prev_data[0],prev_data[1],prev_data[2]
    display.text(str(round(prev_power,4)),70,0,0)
    display.text(str(round(prev_voltage,4)),70,24,0)
    display.text(str(round(prev_current,4)),70,48,0)
    # write the new stuff
    display.text(str(round(power,4)),70,0,1)
    display.text(str(round(voltage,4)),70,24,1)
    display.text(str(round(current,4)),70,48,1)
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

### for debug only
# class INA219:
#     def __init__(self):
#         self.voltage = 0.100
#         self.current = 0.219
#         self.power = self.voltage * self.current
        
#     def fluctuate_voltage(self,input):
#         self.voltage = self.voltage + input
#         self.power = self.voltage * self.current
        
#     def fluctuate_current(self,input):
#         self.current = self.current + input
#         self.power = self.voltage * self.current
# ina = INA219()
# randomlist = []
# for i in range(0,1000):
#     n = random.randint(-1,1)
#     randomlist.append(n)

# setup ina219 
SHUNT_OHMS = 0.1  # Check value of shunt used with your INA219
ina = INA219(SHUNT_OHMS,i2c_sensor)
I2C_INTERFACE_NO = 2
ina = INA219(SHUNT_OHMS,I2C(I2C_INTERFACE_NO))
ina.configure()
# write displays never changing functions 
write_display_nonchanging_sections()
# measure and display loop
run_loop = 1
passed_rnd_1 = False

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
        if passed_rnd_1:
            prev_data = rewrite_display(ina.voltage,ina.current,ina.power,prev_data)
        else:
            prev_data = rewrite_display(ina.voltage,ina.current,ina.power,[0,0,0])
            passed_rnd_1 = True
        time.sleep_ms(200)


# circuit python version
# sudo pip3 install adafruit-circuitpython-ina219
# import board
# import busio 
# import adafruit_ina219  

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