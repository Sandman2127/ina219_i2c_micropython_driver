# use micropython

from random import randint
import time
from machine import I2C,Pin
import ssd1306
from micropython import const

config_address = 0 #'00'
shunt_voltage_address = 1 #'01'
voltage_address = 2 #'02'  # hex(2) == '0x2'
current_address = 3 #'03'
power_address = 4 #'04'
                            
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
    
def convert_v_byte(byte_data):
    return byte_data

def convert_i_byte(byte_data):
    return byte_data

def convert_power_byte(byte_data):
    return byte_data

def return_bytearray_of_address(int_address):
    return bytearray(bytes.fromhex('0' + str(int_address))) # takes 2 --> '02' --> b'\x02'

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

### for debug only
if debug == 1:
    class INA219:
         def __init__(self):
             self.voltage = 0.100
             self.current = 0.219
             self.power = self.voltage * self.current
            
         def fluctuate_voltage(self,input):
             self.voltage = self.voltage + input
             self.power = self.voltage * self.current
            
         def fluctuate_current(self,input):
             self.current = self.current + input
             self.power = self.voltage * self.current
    ina = INA219()
    randomlist = []
    for i in range(0,1000):
         n = randint(-1,1)
         randomlist.append(n)
else:
    class INA219:
        def __init__(self,address_in):
            self.peripheral_address = address_in
            print("Peripheral address:",self.peripheral_address)
            self.voltage = 0
            self.current = 0
            self.power = 0 
            # initiate communication with the device
            startup_buffer = bytearray([0x399F])  # '00111001 10011111' 
            # 0 is the configuration address 
            i2c_sensor.writeto_mem(self.peripheral_address,config_address,startup_buffer)
            
        def change_pointer_mem_address(self,mem_address):
            print("changing pointer mem_address to:",mem_address)
            print("mem address as a byte array:",return_bytearray_of_address(mem_address))
            i2c_sensor.writeto(self.peripheral_address,return_bytearray_of_address(mem_address)) 

        def get_voltage(self):
            voltage_byte = i2c_sensor.readfrom_mem(self.peripheral_address,voltage_address,2) # read 2 bytes from the voltage mem address from the peripheral device
            self.voltage = convert_v_byte(voltage_byte)
            time.sleep_ms(1)
        def get_current(self):
            current_byte = i2c_sensor.readfrom_mem(self.peripheral_address,current_address,2) # read 2 bytes from the current mem address from the peripheral device
            self.current = convert_i_byte(current_byte)
            time.sleep_ms(1)
        def get_power(self):
            power_byte = i2c_sensor.readfrom_mem(self.peripheral_address,power_address,2)  # read 2 bytes from the current mem address from the peripheral device
            self.power = convert_power_byte(power_byte)
            time.sleep_ms(1)
        """
            ina219 specific data:
            0x399F = 00111001 10011111
            POINTER_ADDRESS REGISTER_NAME FUNCTION BINARY HEX
            00  Configuration   All-register reset, settings for bus voltage range, PGA Gain, ADC resolution/averaging.00111001 10011111 399F R/W
            01  Shunt voltage   Shunt voltage measurement data.Shunt voltage — R
            02  Bus voltage Bus voltage measurement data.Bus voltage — R
            03  Power (2)   Power measurement data.00000000 000000000000 R
            04  Current(2)  Contains the value of the current flowing through the shunt resistor.00000000 000000000000 R
            05  Calibration Sets full-scale range and LSB of current and power measurements. Overall system calibration.00000000 000000000000 R/W

            I2C operations: https://docs.micropython.org/en/latest/library/machine.I2C.html

            i2c = I2C(freq=400000)          # create I2C peripheral at frequency of 400kHz
                                            # depending on the port, extra parameters may be required
                                            # to select the peripheral and/or pins to use

            i2c.scan()                      # scan for peripherals, returning a list of 7-bit addresses

            i2c.writeto(42, b'123')         # write 3 bytes to peripheral with 7-bit address 42
            i2c.readfrom(42, 4)             # read 4 bytes from peripheral with 7-bit address 42

            i2c.readfrom_mem(42, 8, 3)      # read 3 bytes from memory of peripheral 42,
                                            #   starting at memory-address 8 in the peripheral
            i2c.writeto_mem(42, 2, b'\x10') # write 1 byte to memory of peripheral 42
                                            #   starting at address 2 in the peripheral
            Memory operations¶
            Some I2C devices act as a memory device (or set of registers) that can be read from and written to.
            In this case there are two addresses associated with an I2C transaction: the peripheral address and the memory address.
            The following methods are convenience functions to communicate with such devices.

            I2C.readfrom_mem(addr, memaddr, nbytes, *, addrsize=8)
                
            Read nbytes from the peripheral specified by addr starting from the memory address specified by memaddr.
            The argument addrsize specifies the address size in bits. Returns a bytes object with the data read.

            I2C.readfrom_mem_into(addr, memaddr, buf, *, addrsize=8)
                
            Read into buf from the peripheral specified by addr starting from the memory address specified by memaddr.
            The number of bytes read is the length of buf. The argument addrsize specifies the address size in bits (on ESP8266 this argument is not recognised and the address size is always 8 bits).

            The method returns None.

            I2C.writeto_mem(addr, memaddr, buf, *, addrsize=8)
                
            Write buf to the peripheral specified by addr starting from the memory address specified by memaddr.
            The argument addrsize specifies the address size in bits (on ESP8266 this argument is not recognised and the address size is always 8 bits).

            The method returns None.
        """
            
    # setup ina219
    SHUNT_OHMS = 0.1 
    ina = INA219(devices[1]) # should be 2nd i2c device i.e. the ina219
    
# write displays never changing functions 
write_display_nonchanging_sections()
# measure and display loop
run_loop = 1
passed_rnd_1 = False


if len(devices) == 0:
     print("No i2c device !")
else:
     print('found:',len(devices),'i2c devices')
     cnt = 0
     for dev in devices:
         print("device:",cnt,dev,hex(dev))
         cnt += 1

voltage_display = True
current_display = False
power_display = False
shunt_display = False
while True:
    ### for the micropython  ### 
    # print("Bus Voltage: %.3f V" % ina.voltage())
    # print("Current: %.3f mA" % ina.current())
    # print("Power: %.3f mW" % ina.power())

    # Check internal calculations haven't overflowed (doesn't detect ADC overflows)
    # if not ina.voltage:
    #     print("Internal Overflow Detected!")
    #     print("")
    if voltage_display:
        ina.change_pointer_mem_address(voltage_address)
        ina.get_voltage()
        print(list(ina.voltage))
    elif current_display:
        ina.change_pointer_mem_address(current_address)
        ina.get_current()
        print(list(ina.current))
    elif power_display:
        ina.change_pointer_mem_address(power_address)
        ina.get_power()
        print(list(ina.power))
    elif shunt_display:
        ina.change_pointer_mem_address(shunt_voltage_address)
        ina.get_power()
        print(list(ina.power))
        # if passed_rnd_1:
        #     prev_data = rewrite_display(ina.voltage,ina.current,ina.power,prev_data)
        # else:
        #     prev_data = rewrite_display(ina.voltage,ina.current,ina.power,[0,0,0])
        #     passed_rnd_1 = True
        time.sleep_ms(1000)
    time.sleep_ms(1000)


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