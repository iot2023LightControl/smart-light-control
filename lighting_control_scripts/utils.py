import requests
from datetime import datetime
import re
from dataclasses import dataclass
from yeelight import discover_bulbs
from yeelight import Bulb
from yeelight import LightType
import time
import pytz

def switch_lamps(lamp_on = True):
    url = "http://10.2.2.2:1880/knx/floor_1/room_102/lights/group4"
    
    data = {"state": lamp_on}
   
    try:
        response = requests.post(url, json=data)
        print("try the lamp", response)
        # Check the status code to ensure the request was successful
        if response.status_code != 201:
            print(f"Request lamp_on {lamp_on} failed with status code: {response.status_code}")
       
    except Exception as e:
        print(f"An error occurred when lamp_on {lamp_on}: {e}")


def roll_up_blinds(action = "up"):
    url = "http://10.2.2.2:1880/knx/floor_1/room_102/blinds/group14"
    
    data = {"action": action}

    try:
        response = requests.post(url, json=data)

        # Check the status code to ensure the request was successful
        if response.status_code != 201:
            print(f"Action {action} failed with status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred when doing action {action}: {e}")



@dataclass
class dpp3e_data_packet:
    """Class for DPP3e data packets"""
    timestamp : int = 0
    veml7700_lux: int = 0
    sgp40_voc: int = 0
    shtc3_temperature: int = 0
    shtc3_humidity: int = 0
    as7262_temp: float = 0
    as7262_violet: float = 0
    as7262_blue: float = 0
    as7262_green: float = 0
    as7262_yellow: float = 0
    as7262_orange: float = 0
    as7262_red: float = 0
    veml6070_uv: int = 0
    si1145_lux: int = 0
    si1145_infrared: int = 0
    si1145_uv: int = 0
    values_set : int = 0
    
    def cct_calculation_as7262(self) -> float:
        #We use coefficients from the datasheet of AMS TCS3414CS 
        #The RGB channels of AMS TCS3414CS are roughly at 450nm, 550nm, 625nm
        #https://ams.com/documents/20143/80162/TCS34xx_AN000517_1-00.pdf
        #The 6 channels on the AS7262 are at 450nm(V),500nm, 550nm(G), 570nm, 600nm, and 650nm(R). T
        #Step 1: map the VGB channel response to the CIE tristimulus values, XYZ.
        #get RGV response of sensor as7262
        
        V = self.as7262_violet
        G = self.as7262_green
        R = self.as7262_red

        X = -0.14282 * R + 1.54924 * G + -0.95641 * V
        Y = -0.32466 * R + 1.57837 * G + -0.73191 * V
        Z = -0.68202 * R + 0.77073 * G + 0.56332 * V

        #Step 2: calculate the chromaticity coordinates
        x = X/(X + Y + Z)
        y = Y/(X + Y + Z)

        #Step 3: McCamy’s formula (third version)
        #https://onlinelibrary.wiley.com/doi/epdf/10.1002/col.5080170211
        n = (x - 0.3320) / (0.1858 - y)
        cct = 449 * n**3 + 3525 * n**2 + 6823.3 * n + 5520.33
        return cct

#Choose the mode
debug_mode = 1
if debug_mode == 0:
    def PRINT(x):
        return
if debug_mode == 1:
    def PRINT(x):
        print(x)
def write_csv(filename, line):
    with open(filename, 'a',newline = '\n') as f:
        f.write(f"{[current_time_string(),str(int(time.time()))]}{str(line)}\n")

def extract_data(filename, line, data_packet):
    if re.search('DataApollo', line):
        data = line.split()[5:-1]
        data_string = " ".join(data)
        write_csv(filename, data_string)
        for field, value in zip(data[0::2], data[1::2]):
            if (re.match('Timestamp', field)):
                data_packet.timestamp = int(value)
                data_packet.values_set += 1
            elif (re.match('veml7700_lux', field)):
                data_packet.veml7700_lux = int(value)
                data_packet.values_set += 1
            elif (re.match('sgp40_voc', field)):
                data_packet.sgp40_voc = int(value)
                data_packet.values_set += 1
            elif (re.match('shtc3_temperature', field)):
                data_packet.shtc3_temperature = int(value)
                data_packet.values_set += 1
            elif (re.match('shtc3_humidity', field)):
                data_packet.shtc3_humidity = int(value) 
                data_packet.values_set += 1           
            elif (re.match('as7262_temp', field)):
                data_packet.as7262_temp = int(value)
                data_packet.values_set += 1
            elif (re.match('as7262_violet', field)):
                data_packet.as7262_violet = int(value)
                data_packet.values_set += 1
            elif (re.match('as7262_blue', field)):
                data_packet.as7262_blue = int(value)
                data_packet.values_set += 1
            elif (re.match('as7262_green', field)):
                data_packet.as7262_green = int(value)
                data_packet.values_set += 1
            elif (re.match('as7262_yellow', field)):
                data_packet.as7262_yellow = int(value)
                data_packet.values_set += 1
            elif (re.match('as7262_orange', field)):
                data_packet.as7262_orange = int(value)
                data_packet.values_set += 1
            elif (re.match('as7262_red', field)):
                data_packet.as7262_red = int(value)
                data_packet.values_set += 1
            elif (re.match('veml6070_uv', field)):
                data_packet.veml6070_uv = int(value)
                data_packet.values_set += 1
            elif (re.match('si1145_lux', field)):
                data_packet.si1145_lux = int(value)
                data_packet.values_set += 1
            elif (re.match('si1145_infrared', field)):
                data_packet.si1145_infrared = int(value)
                data_packet.values_set += 1
            elif (re.match('si1145_uv', field)):
                data_packet.si1145_uv = int(value)
                data_packet.values_set += 1
            elif (re.match('values_set', field)):
                data_packet.values_set = int(value)
                data_packet.values_set += 1
        return True
    else: 
        return False


def current_time_string():
    return datetime.now(pytz.timezone("Europe/Paris")).strftime("%H:%M:%S")

#bulb object initialization
def bulb_initialization(ip, brightness, cct):
    #set auto_on() to be off to save commands
    bulb = Bulb(ip, auto_on = False)
    bulb.turn_on()
    bulb.set_brightness(brightness) 
    bulb.set_color_temp(cct) 
    return bulb

def bulb_power(bulb):
    return bulb.get_properties()['power']

def adapt_illuminance(bulb, illuminance, brightness, illuminance_threshold_low, illuminance_threshold_high):
    #increase the brightness by 10% each time
    PRINT('Adapting the illuminance.')
    PRINT(f'The current brightness level of the bulb is {brightness} %')
    if illuminance < illuminance_threshold_low:
        PRINT(f"The illuminance is too low: {illuminance}")
        # to ensure the bulb is on 
        if bulb_power(bulb) == 'off':
            bulb.turn_on()  
            bulb.set_brightness(50) 
            bulb.set_color_temp(4500) 
            PRINT("The lamp is turned on and set to 50% brightness and 4500 K.")
            return
        elif bulb_power(bulb) == 'on' and brightness < 100:
            brightness += 10
            brightness = min(brightness, 100)
            bulb.set_brightness(brightness) 
            bulb_properties = bulb.get_properties()
            PRINT(f'The increased actual brightness of the bulb is {float(bulb_properties["current_brightness"])}, the cct is {float(bulb_properties["ct"])}.')
            return 
    #decrease the brightness by 10% each time
    elif illuminance > illuminance_threshold_high:
       PRINT(f"The illuminance is too high: {illuminance}")
       if (bulb_power(bulb) == 'on' and brightness > 1):
        #only decrease the brightness if the bulb is on
            brightness -= 10
            bulb.set_brightness(brightness) 
            bulb_properties = bulb.get_properties()
            PRINT(f'The decreased actual brightness of the bulb is {float(bulb_properties["current_brightness"])}, the cct is {float(bulb_properties["ct"])}.')
            if brightness <= 1:
                bulb.turn_off()
            return    

       
def adapt_cct(bulb, cct, degrees, cct_threshold_low, cct_threshold_high):
    """It was ensured that the bulb is on."""
    PRINT('Adapting the cct.')
    PRINT(f'The current ambient cct is of {cct} Kelvin.')
    if cct < cct_threshold_low and degrees < 6500:
        degrees += 50
        degrees = min(degrees, 6500)
        bulb.set_color_temp(degrees)
        bulb_properties = bulb.get_properties()
        PRINT(f'The increased cct of the bulb is {float(bulb_properties["ct"])}, the brightness is {float(bulb_properties["current_brightness"])}.')
    elif cct > cct_threshold_high and degrees > 2700:
        degrees -= 50
        degrees = max(degrees, 2700)
        bulb.set_color_temp(degrees)
        bulb_properties = bulb.get_properties()
        PRINT(f'The decreased cct of the bulb is {float(bulb_properties["ct"])}, the brightness is {float(bulb_properties["current_brightness"])}.')

def target_light_property_at_time(current_time, illuminance = True):
    # Convert current_time to hours (e.g., 9.5 for 9:30 am)
    current_hour = current_time.hour + current_time.minute / 60.0

    # Schedule points and illuminance values
    hours = [9, 12, 13, 14, 16, 17]
    turning_point_values = [1000, 500, 500, 1000, 500, 500]
    if not illuminance:
        turning_point_values = [5000, 4000, 4000, 5000, 4000, 4000] 
    # Linear interpolation function
    def linear_interpolation(x, x0, x1, y0, y1):
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0)

    # Check the current time and interpolate the illuminance accordingly
    if current_hour < hours[0] or current_hour >= hours[-1]:
        if illuminance:
            return 450, 550  # Default return None for any other cases
        else:
            return 3700, 4300
    for i in range(len(hours) - 1):
        if hours[i] <= current_hour < hours[i + 1]:
            target_value = linear_interpolation(
                current_hour, hours[i], hours[i + 1], turning_point_values[i], turning_point_values[i + 1]
            )
            if illuminance:
                return target_value - 50, target_value + 50
            else:
                return target_value - 300, target_value + 300

    

