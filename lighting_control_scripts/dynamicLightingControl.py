import serial
import serial.tools.list_ports as ports
from datetime import datetime
import re
from dataclasses import dataclass
from yeelight import discover_bulbs
from yeelight import Bulb
from yeelight import LightType
import time
import pytz
import utils
import math


log_filename  = datetime.now(pytz.timezone("Europe/Paris")).strftime('dynamic_monitorlog_%Y-%m-%d.txt')       
com_ports = list(ports.comports())  # create a list of com ['COM1','COM2']
for i in com_ports:
    utils.PRINT(i.device)  # returns 'COMx'

ser = serial.Serial(
    port='/dev/ttyUSB1',\
    baudrate=1000000,\
    parity=serial.PARITY_NONE,\
    stopbits=serial.STOPBITS_ONE,\
    bytesize=serial.EIGHTBITS,\
        timeout=0)
if not ser.isOpen():
    ser.open()

print("connected to: " + ser.portstr)

try:
    bulb_color = utils.bulb_initialization('10.2.2.193', 50, 6500)
except Exception as e:
    utils.PRINT(e)
    exit()
data_packet = utils.dpp3e_data_packet()
csv_writer_lamp_offline = 0

while True: 
    line = ser.readline()
    if line:
        line = str(line)
        utils.PRINT(line)

        if utils.extract_data(log_filename, line, data_packet):
            #get properties
            if data_packet.values_set >= 16:
                try:
                    illuminance = data_packet.veml7700_lux
                    cct = data_packet.cct_calculation_as7262()
                    brightness = float(bulb_color.get_properties()["current_brightness"])
                    degrees = float(bulb_color.get_properties()["ct"]) #min 2700, max 6500
                    is_on = utils.bulb_power(bulb_color) == 'on'

                    time_now = datetime.now(pytz.timezone("Europe/Paris"))
                    # only run the system from 9am to 5pm
                    if time_now.hour >= 9 and time_now.hour < 17: 
                        target_illuminance_low, target_illuminance_high = utils.target_light_property_at_time(time_now, illuminance = True)
                        # target_cct_low, target_cct_high = utils.target_light_property_at_time(time_now, illuminance = False)

                        # illuminance adjustment has higher priority over cct adjustment
                        if (illuminance < target_illuminance_low and (not is_on)) \
                            or (illuminance < target_illuminance_low and is_on and brightness < 100) \
                                or (illuminance > target_illuminance_high and is_on):
                                utils.adapt_illuminance(bulb_color, illuminance, brightness, target_illuminance_low, target_illuminance_high)
                        
                        #only adjust CCT when the lamp is on.
                        # if is_on:
                        #     if (math.isnan(cct)) or (cct < 2000) or (cct > 8000):
                        #         utils.PRINT(f"Abnormal cct value {cct}, do not change CCT.")
                        #     elif (cct < target_cct_low and degrees <= 6500) or (cct > target_cct_high and degrees >= 2700):
                        #         utils.adapt_cct(bulb_color, cct, degrees, target_cct_low, target_cct_high)
                       

                    #make sure the lamps are off during non-working hours
                    else:   
                        # make sure the smart lamps are off
                        if utils.bulb_power(bulb_color) == "on":
                            bulb_color.turn_off()

                    data_packet = utils.dpp3e_data_packet()

                    if csv_writer_lamp_offline:
                        utils.write_csv(log_filename, "Lamp is back online!")
                        csv_writer_lamp_offline = 0
                except Exception as e:
                    utils.PRINT(f"Error: {e}")
                    if not csv_writer_lamp_offline:
                        utils.write_csv(log_filename, "Lamp is off!")
                        csv_writer_lamp_offline = 1
                    else:
                        #Don't write anything here to prevent huge file size.
                        continue

ser.close()

