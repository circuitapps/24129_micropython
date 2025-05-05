
from machine import Pin, SoftI2C
import time
import urtc  # RTC DS3231 library from Adafruit
import images

class RTC:
    def __init__(self, DS3231_RTC_ADDRESS, scl_pin, sda_pin):
        i2c = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.rtc = urtc.DS3231(i2c, address=DS3231_RTC_ADDRESS)  # Check to see additional RTC devices supported by this library.
        self.cur_time={'month' : f"{0:02d}",
                    'day' : f"{0:02d}",
                    'year' : f"{0:02d}",
                    'hour' : f"{0:02d}",
                    'minute' : f"{0:02d}",
                    'second' : f"{0:02d}",
                    }
    
        self.cur_temp = 0.00  # in deg C

    def get_RTC_time(self, display=False):
        cur_datetime = self.rtc.datetime()

        self.cur_time['month'] = f"{cur_datetime.month:02d}"
        self.cur_time['day'] = f"{cur_datetime.day:02d}"
        self.cur_time['year'] = f"{cur_datetime.year - 2000:02d}"  # Storing in YY format

        self.cur_time['hour'] = f"{cur_datetime.hour:02d}"
        self.cur_time['minute'] = f"{cur_datetime.minute:02d}"
        self.cur_time['second'] = f"{cur_datetime.second:02d}"

        if display:
            print(f"Current RTC time (MM/DD/YY, HH:MM:SS):: {cur_datetime.month:02d}/{cur_datetime.day:02d}/{cur_datetime.year - 2000}, {cur_datetime.hour:02d}:{cur_datetime.minute:02d}:{cur_datetime.second:02d}")

    def get_temperature(self, display=False):
        cur_temp_in_degC = self.rtc.temperature()
        self.cur_temp = f"{cur_temp_in_degC:.01f}"

        fahrenheit = cur_temp_in_degC * (9/5) + 32

        if display:
            print(f"Current RTC temperature:: {cur_temp_in_degC:.01f} degC")
        
        return cur_temp_in_degC, fahrenheit

    def update_RTC(self):
        time_tuple= time.localtime()
        print(f"tuple: {time_tuple}")
        time_seconds = time.mktime(time_tuple)
        time_tuple = urtc.seconds2tuple(time_seconds)
        self.rtc.datetime(time_tuple)  # sync the RTC hardware over I2C

    def get_time_list(self, mode = 'date'):
        """
        Reads current time and returns digits.
        
        If mode = date, expecting time_list =[y,Y,11,d,D,11,m,M] Note: Number 11 is the code for the delimiter
        else expecting time_list =[s,S,10,m,M,10,h,H] Note: Number 10 is the code for the delimiter
        """

        time_list = []
        self.get_RTC_time()  # read time from RTC device

        if mode == 'date':
            MSD, LSD = divmod(int(self.cur_time['year']), 10)  # Most and Least significant digits retrieved
            time_list.append(LSD)
            time_list.append(MSD)
            time_list.append(images.special_symbol_codes['slash'])  # Special code for slash delimiter added to list

            MSD, LSD = divmod(int(self.cur_time['day']), 10)  # Most and Least significant digits retrieved
            time_list.append(LSD)
            time_list.append(MSD)
            time_list.append(images.special_symbol_codes['slash'])  # Special code for slash delimiter added to list

            MSD, LSD = divmod(int(self.cur_time['month']), 10)  # Most and Least significant digits retrieved
            time_list.append(LSD)
            time_list.append(MSD)    
        else:
            MSD, LSD = divmod(int(self.cur_time['second']), 10)  # Most and Least significant digits retrieved
            time_list.append(LSD)
            time_list.append(MSD)
            time_list.append(images.special_symbol_codes['colon'])   # Special code for colon delimiter added to list

            MSD, LSD = divmod(int(self.cur_time['minute']), 10)  # Most and Least significant digits retrieved
            time_list.append(LSD)
            time_list.append(MSD)
            time_list.append(images.special_symbol_codes['colon'])  # Special code for colon delimiter added to list

            MSD, LSD = divmod(int(self.cur_time['hour']), 10)  # Most and Least significant digits retrieved
            time_list.append(LSD)
            time_list.append(MSD)
        
        return time_list    