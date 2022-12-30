# use micropython

from random import randint
import time
from machine import I2C,Pin
import ssd1306
from micropython import const
from math import trunc

config_address = 0 #'00'
shunt_voltage_address = 1 #'01'
voltage_address = 2 #'02'  # hex(2) == '0x2'
current_address = 3 #'03'
power_address = 4 #'04'
calibration_address = 5 #'05'
mv_voltage_bus_resolution = 4 # 4 mv
max_expected_amperage = 2.000 # 2 amps
current_lsb = max_expected_amperage/(2**15)  # 2 amps max yields 0.000061035 A or 610uA resolution
shunt_resistance = 0.1 # ohms
calibration_val = trunc((0.04096/(current_lsb * shunt_resistance))) # == 6710 max expected value used for calibration
                            
def rewrite_display(voltage,current,power):
    # https://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html
    # overwrite the old stuff
    #display.fill_rect(x,y,w,h,c):
    display.fill_rect(70, 0, 58, 12, 0)
    display.fill_rect(70, 24, 58, 12, 0)
    display.fill_rect(70, 48, 58, 12, 0)
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
    


def number_to_bytearray(number):
    #if number > 255 :
    #    n_hex = hex(number).replace('0x','') # hex string like '0x1a36' --> split to --> '1a36'
    #    n_hex_byte1 = n_hex[:2]           # hex string like '1a36' --> split to --> '1a'
    #    n_hex_byte2 = n_hex[2:]           # hex string like '1a36' --> split to --> '36'
        #print(n_hex_byte1,n_hex_byte2)
    #    print([int(n_hex_byte1,16) << 8,int(n_hex_byte2,16)])
    #    bytearray_out = bytearray([int(n_hex_byte1,16) << 8,int(n_hex_byte2,16)])
    #else:
    n_hex = hex(number).replace('0x','') # hex string like '0x2' --> split to --> '2'
    bytearray_out = bytearray.fromhex(n_hex)
    
    return bytearray_out 

def bytearray_of_register_address(int_address): 
        return bytearray.fromhex('0' + str(int_address))

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
            print("Config address:",config_address)
            self.voltage = 0
            self.current = 0
            self.power = 0 
            # initiate communication with the device:
            # setup configuration, 0 is the config address
            configuration_array = bytearray.fromhex('399F')  # '00111001 10011111' == 14751 >>> ba = bytearray.fromhex('399F') # ba[0] << 8 | ba[1] == 14751 
            #configuration_array = bytearray.fromhex('399F')
            i2c_sensor.writeto_mem(self.peripheral_address,config_address,configuration_array)
            # setup current calibration, 5 is the calibration address
            # calibration value: 6710 --> hex: '0x1a36' --> '1a36' --> bytes array: bytearray(b'\x1a6') --> list(calibration_array) --> [24,26] --> >>> 24 << 8 | 26 == 6710
            calibration_array = number_to_bytearray(calibration_val)
            print("Calibration address:",calibration_address)
            print("Calibration value:",calibration_val,"\nCalibration value binary:",bin(calibration_val),"\nCalibration bytarray:",calibration_array)
            i2c_sensor.writeto_mem(self.peripheral_address,calibration_address,calibration_array) 
        
        def change_pointer_mem_address(self,mem_address):
            #print("changing pointer mem_address to:",mem_address)
            #print("mem address as a byte array:",return_bytearray_of_address(mem_address))
            i2c_sensor.writeto(self.peripheral_address,bytearray_of_register_address(mem_address))
            
        def convert_measured_bytes(self,byte1_int,byte2_int,measurment_type):
            if measurment_type == 'voltage':
                # shift left 5 to clear the first byte and right 3 to remove irrelevant data
                output_voltage = (int(byte1_int << 5 | byte2_int >> 3) * mv_voltage_bus_resolution)/1000
                return output_voltage
            elif measurment_type == 'current':
                # shift left 8 to clear the first byte and right 1 to remove sign data
                # Current Register = Shunt Voltage Register * Calibration Register / 4096
                # output_current = ((byte1_int << 8 | byte2_int) >> 1) * calibration_val / 4096
                # empirically determined scaling from the function output_current = 0.3421655(returned_2_byte_value * current_lsb )^ 0.5355997
                output_current = (0.3421655 * ((byte1_int << 8 | byte2_int) >> 1) * current_lsb)**0.5355997
                return output_current
            elif measurment_type == "power":
                output_power = int(byte1_int << 8 | byte2_int) * mv_voltage_bus_resolution
                return output_power 

        def get_voltage(self):
            voltage_bytes = i2c_sensor.readfrom_mem(self.peripheral_address,voltage_address,2) # read 2 bytes from the voltage mem address from the peripheral device
            vbyte1_int,vbyte2_int = list(voltage_bytes)[0],list(voltage_bytes)[1]
            #print("vbytes:",voltage_bytes,"\nvbyte1:",vbyte1_int,"\nvbyte2:",vbyte2_int)
            self.voltage = self.convert_measured_bytes(vbyte1_int,vbyte2_int,'voltage')
            time.sleep_ms(10)
        def get_current(self):
            #current_bytes = list(i2c_sensor.readfrom_mem(self.peripheral_address,shunt_voltage_address,2)) # read 2 bytes from the current mem address from the peripheral device
            current_bytes = list(i2c_sensor.readfrom_mem(self.peripheral_address,current_address,2))
            cbyte1_int,cbyte2_int = current_bytes[0],current_bytes[1]
            print("cbytes:",current_bytes,"\ncbyte1:",cbyte1_int,"\ncbyte2:",cbyte2_int)
            self.current = self.convert_measured_bytes(cbyte1_int,cbyte2_int,'current')
            time.sleep_ms(10)
        def get_power(self):
            power_bytes = list(i2c_sensor.readfrom_mem(self.peripheral_address,power_address,2))  # read 2 bytes from the power mem address from the peripheral device
            pbyte1_int,pbyte2_int = power_bytes[0],power_bytes[1]
            self.power = self.convert_measured_bytes(pbyte1_int,pbyte2_int,'power')
            time.sleep_ms(10)
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
            The number of bytes read is the length of buf. The argument addrsize specifies the address size in bits (on ESP8266 this argument is not
            recognised and the address size is always 8 bits).

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
            ina.change_pointer_mem_address(voltage_address)
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
            ina.change_pointer_mem_address(current_address)
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
            ina.change_pointer_mem_address(power_address)
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
