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


ILLUMINANCE_THRESHOLD_LOW = 500
ILLUMINANCE_THRESHOLD_HIGH = 1000
CCT_THRESHOLD_LOW = 4000
CCT_THRESHOLD_HIGH = 5000


log_filename  = datetime.now(pytz.timezone("Europe/Paris")).strftime('monitorlog_%Y-%m-%d.txt')       
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
                    if time_now.hour >= 8 and time_now.hour < 17: 

                        # status 1: smart light control for 10min
                        # if (time_now.minute >= 0 and time_now.minute < 10) \
                        #     or (time_now.minute >= 30 and time_now.minute < 40):

                        if (time_now.minute >= 0 and time_now.minute < 10) \
                            or (time_now.minute >= 20 and time_now.minute < 30) \
                            or (time_now.minute >= 40 and time_now.minute < 50):
                            # make sure the normal lamps are off
                            # utils.switch_lamps(False)

                            # illuminance adjustment has higher priority over cct adjustment
                            if (illuminance < ILLUMINANCE_THRESHOLD_LOW and (not is_on)) \
                                or (illuminance < ILLUMINANCE_THRESHOLD_LOW and is_on and brightness < 100) \
                                    or (illuminance > ILLUMINANCE_THRESHOLD_HIGH and is_on):
                                utils.adapt_illuminance(bulb_color, illuminance, brightness, 500, 1000)
                               
                            # else:
                                #only adjust when the lamp is on.
                                # if is_on:
                                #     if (cct < CCT_THRESHOLD_LOW and degrees <= 6500) or (cct > CCT_THRESHOLD_HIGH and degrees >= 2700):
                                #         utils.adapt_cct(bulb_color, cct, degrees, 4000, 5000)
                        # status 2: normal lamps on for 10min
                        # elif (time_now.minute >= 10 and time_now.minute < 20) \
                        #     or (time_now.minute >= 40 and time_now.minute < 50):
                        #     if utils.bulb_power(bulb_color) == "on":
                        #         bulb_color.turn_off()
                            
                        #     utils.switch_lamps(True)
                        
                        # status 3: no lamps
                        else:
                            # utils.switch_lamps(False)
                            if utils.bulb_power(bulb_color) == "on":
                                bulb_color.turn_off()

                    #make sure the lamps are off during non-working hours
                    else:   
                        # make sure the normal lamps are off
                        # utils.switch_lamps(False)
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

