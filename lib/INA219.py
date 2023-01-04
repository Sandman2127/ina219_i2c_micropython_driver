# The MIT License (MIT)
#
# Copyright (c) 2022 Dean Sanders 
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from micropython import const
from time import sleep_ms
from math import e

class INA219:
    def __init__(self,sensor_configuration,device_address_in,shunt_res,lsb,bus_resolution_mv,calibration_value):
        # input required variables stuff
        self.i2c_sensor = sensor_configuration # effectively the object generated from i2c_sensor = I2C(0,sda=sda_screen,scl=scl_screen,freq=400000)
        self.peripheral_address = device_address_in
        self.current_lsb = lsb
        self.mv_voltage_bus_resolution = bus_resolution_mv
        self.calibration_value = calibration_value
        
        # measured values
        self.shunt_resistance = shunt_res
        self.PGA8_resolution = 0.00001 # 10 uV
        self.voltage = 0
        self.current = 0
        self.power = 0
        self.shunt_voltage = 0
        
        # ina219 address constants
        self.config_address = const(0) #'00'
        self.shunt_voltage_address = const(1) #'01'
        self.voltage_address = const(2) #'02'  # hex(2) == '0x2'
        self.current_address = const(3) #'03'
        self.power_address = const(4) #'04'
        self.calibration_address = const(5) #'05'
        
        print(" *** INA219 Startup ***")
        print("Peripheral device address:",self.peripheral_address)
        print("Bus device resolution:",self.mv_voltage_bus_resolution,"mV")
        print("Current calibration value:",self.calibration_value)
        
        # initiate communication with the device:
        # setup configuration, 0 is the config address
        configuration_array = bytearray.fromhex('399F') # '00111001 10011111' == 14751 >>> ba = bytearray.fromhex('399F') # ba[0] << 8 | ba[1] == 14751, standard 4mV resolution default startup
        print("Initiating communication with device",self.peripheral_address,"with config address",self.config_address,"using configuration register:",bin(int('399F',16)))
        self.i2c_sensor.writeto_mem(self.peripheral_address,self.config_address,configuration_array)
        
        # setup current calibration, 5 is the calibration address
        # calibration value: 6710 --> hex: '0x1a36' --> '1a36' --> bytes array: bytearray(b'\x1a6') --> list(calibration_array) --> [24,26] --> >>> 24 << 8 | 26 == 6710
        calibration_array = self.number_to_bytearray(self.calibration_value)
        print("Running current calibration using calibration address:",self.calibration_address)
        #print("Calibration value:",calibration_val,"\nCalibration value binary:",bin(calibration_val),"\nCalibration bytarray:",calibration_array)
        print("Corrected Calibration value:",self.calibration_value,"\nCalibration bytearray:",calibration_array)
        self.i2c_sensor.writeto_mem(self.peripheral_address,self.calibration_address,calibration_array) 
    
    def number_to_bytearray(self,number):
        n_hex = hex(number).replace('0x','') # hex string like '0x2' --> split to --> '2'
        bytearray_out = bytearray.fromhex(n_hex)
        return bytearray_out 

    def bytearray_of_register_address(self,int_address): 
        return bytearray.fromhex('0' + str(int_address))

    def change_pointer_mem_address(self,mem_address):
        self.i2c_sensor.writeto(self.peripheral_address,self.bytearray_of_register_address(mem_address))
        
    def convert_measured_bytes(self,byte1_int,byte2_int,measurement_type):
        if measurement_type == 'voltage':
            # shift left 5 to clear the first byte and right 3 to remove irrelevant data
            output_voltage = (int(byte1_int << 5 | byte2_int >> 3) * self.mv_voltage_bus_resolution)/1000
            return output_voltage
        elif measurement_type == 'shunt_voltage':
            # shift left to clear the first byte
            output_shunt_voltage = int(byte1_int << 8 | byte2_int)
            return output_shunt_voltage 

    def get_voltage(self):
        voltage_bytes = self.i2c_sensor.readfrom_mem(self.peripheral_address,self.voltage_address,2) # read 2 bytes from the voltage mem address from the peripheral device
        vbyte1_int,vbyte2_int = list(voltage_bytes)[0],list(voltage_bytes)[1]
        self.voltage = self.convert_measured_bytes(vbyte1_int,vbyte2_int,'voltage')
        
    def get_power(self):
        self.get_voltage()
        self.get_current()
        # P = IV
        self.power = self.voltage * self.current
        
    def get_current(self):
        shunt_voltage_bytes = self.i2c_sensor.readfrom_mem(self.peripheral_address,self.shunt_voltage_address,2)
        sv_byte1_int,sv_byte2_int = list(shunt_voltage_bytes)[0],list(shunt_voltage_bytes)[1]
        self.shunt_voltage = self.convert_measured_bytes(sv_byte1_int,sv_byte2_int,'shunt_voltage')
        # LSB = 10 uV is the limit of resolution at PGA8
        self.current = (self.shunt_voltage * self.PGA8_resolution) / self.shunt_resistance
        
    def get_shunt_voltage(self):
        shunt_voltage_bytes = self.i2c_sensor.readfrom_mem(self.peripheral_address,self.shunt_voltage_address,2)
        sv_byte1_int,sv_byte2_int = list(shunt_voltage_bytes)[0],list(shunt_voltage_bytes)[1]
        self.shunt_voltage = self.convert_measured_bytes(sv_byte1_int,sv_byte2_int,'shunt_voltage') * self.PGA8_resolution
        
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