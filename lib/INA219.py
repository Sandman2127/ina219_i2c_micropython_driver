from micropython import const
from time import sleep_ms

# INA219(devices[1],mv_voltage_bus_resolution,corrected_calibration_val)
class INA219:
    def __init__(self,sensor_configuration,device_address_in,lsb,bus_resolution_mv,calibration_value):
        # input required variables stuff
        self.i2c_sensor = sensor_configuration # effectively the object generated from i2c_sensor = I2C(0,sda=sda_screen,scl=scl_screen,freq=400000)
        self.peripheral_address = device_address_in
        self.current_lsb = lsb
        self.mv_voltage_bus_resolution = bus_resolution_mv
        self.calibration_value = calibration_value
        
        # measured values
        self.voltage = 0
        self.current = 0
        self.power = 0
        
        # ina219 address constants
        self.config_address = const(0) #'00'
        self.shunt_voltage_address = const(1) #'01'
        self.voltage_address = const(2) #'02'  # hex(2) == '0x2'
        self.current_address = const(3) #'03'
        self.power_address = const(4) #'04'
        self.calibration_address = const(5) #'05'
        #mv_voltage_bus_resolution = const(4) # 4 mv
        
        print(" *** INA219 Startup ***")
        print("Peripheral device address:",self.peripheral_address)
        print("Bus device resolution:",self.mv_voltage_bus_resolution,"mV")
        print("Current calibration value:",self.calibration_value)
        # initiate communication with the device:
        
        # setup configuration, 0 is the config address
        configuration_array = bytearray.fromhex('399F') # '00111001 10011111' == 14751 >>> ba = bytearray.fromhex('399F') # ba[0] << 8 | ba[1] == 14751, standard 4mV resolution default startup
        print("Initiating communication with device",self.peripheral_address,"with config address",self.config_address,"using binary configuration array:",bin(int('399F',16)))
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
        #print("changing pointer mem_address to:",mem_address)
        #print("mem address as a byte array:",return_bytearray_of_address(mem_address))
        self.i2c_sensor.writeto(self.peripheral_address,self.bytearray_of_register_address(mem_address))
        
    def convert_measured_bytes(self,byte1_int,byte2_int,measurment_type):
        if measurment_type == 'voltage':
            # shift left 5 to clear the first byte and right 3 to remove irrelevant data
            output_voltage = (int(byte1_int << 5 | byte2_int >> 3) * self.mv_voltage_bus_resolution)/1000
            return output_voltage
        elif measurment_type == 'current':
            # shift left 8 to clear the first byte and right 1 to remove sign data
            # Current Register = Shunt Voltage Register * Calibration Register / 4096
            # output_current = ((byte1_int << 8 | byte2_int) >> 1) * calibration_val / 4096
            # empirically determined function scaling from the function output_current = 0.3421655(returned_2_byte_value * current_lsb )^ 0.5355997
            #output_current = (0.3421655 * ((byte1_int << 8 | byte2_int) >> 1) * current_lsb)**0.5355997
            # hard wired
            detected_output_current = ((byte1_int << 8 | byte2_int)) * self.current_lsb
            # scaling below 8 detected mA where the detected current is inaccurate
            # equations below empirically determined using an Agilent U1271A as the current reference
            if detected_output_current < 0.008:
                return 0.42757*detected_output_current**0.488257
            else:
                return 0.052401*e**(4.3401*detected_output_current)

            return output_current
        elif measurment_type == "power":
            output_power = int(byte1_int << 8 | byte2_int) * mv_voltage_bus_resolution
            return output_power 

    def get_voltage(self):
        voltage_bytes = self.i2c_sensor.readfrom_mem(self.peripheral_address,self.voltage_address,2) # read 2 bytes from the voltage mem address from the peripheral device
        vbyte1_int,vbyte2_int = list(voltage_bytes)[0],list(voltage_bytes)[1]
        self.voltage = self.convert_measured_bytes(vbyte1_int,vbyte2_int,'voltage')
        sleep_ms(10)
    def get_current(self):
        current_bytes = self.i2c_sensor.readfrom_mem(self.peripheral_address,self.current_address,2)
        cbyte1_int,cbyte2_int = list(current_bytes)[0],list(current_bytes)[1]
        #print("cbytes:",current_bytes,"\ncbyte1:",cbyte1_int,"\ncbyte2:",cbyte2_int)
        self.current = self.convert_measured_bytes(cbyte1_int,cbyte2_int,'current')
        sleep_ms(10)
    def get_power(self):
        self.get_voltage()
        self.get_current()
        # P = IV
        self.power = self.voltage * self.current
        sleep_ms(10)
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