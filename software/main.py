from machine import Pin, SoftI2C, ADC
import time
import ssd1306_helper as oled
import urtc_helper as uh
import uasyncio as asyncio
import system_manager as sm
import images
import main_helper as mh
import display_update_helper as duh
import sdcard_helper as sdh

wifi_credents = {'ssid':'from sdcard', 'password':'from sdcard'}   # This will be populated using the file on SDCard in main

I2C_0_SDA_PIN = 0  # GPIO 0 on pico pi w
I2C_0_SCL_PIN = 1  # GPIO 1 on pico pi w

SDCARD_PORT_CONFIG = {
  'SPI_BUS': 0, # Using SPI port 0 on Pi Pico W
  'SCK_PIN': 2, # GPIO 2
  'MOSI_PIN': 3, # GPIO 3
  'MISO_PIN': 4, # GPIO 4
  'CS_PIN': 5, # GPIO 5 
}

PI_PICO_TEMP_SENSOR = ADC(4)  # Pi Pico has temperature sensor connected to ADC(4) pin
BUTTON_1_PIN = 16 # GPIO 16 on pi pico w. Internal pull down INPUT pin.
DEBOUNCE_DELAY_MS = 100  # button debounce delay in millisecond. Adjust as needed.

DS3231_RTC_ADDRESS=0x68
DS3231_EEPROM_ADDRESS=0x57  # for direct access to EEPROM, if needed
I2C_MUX_ADDRESS=0x70      # This can be any value between 0x70 and 0x77 depending on the A0, A1, A2 settings on the I2C mux hardware.
OLED_128x64_I2C_ADDR=0x3C  # Found by running  address scan with individual screen attached
FIXED_SCREEN_ADDRESS=OLED_128x64_I2C_ADDR # All OLED displays will have this same address < See datasheet for Address; 0x3C for 128x64, 0x3D for 128x32

# Menu selection list
menu_items = ['RESET_TIME_OVER_WIFI', 'GO TO_DARK_MODE', 'LET_THERE_BE_LIGHT !']  # These are the messages to be shown as menu items to user at each button press

# Notification messages
notification_messages = {
  'rtc_update' : "wait_for_wifi_conn",
  'retry_update': "Oops!_retry"
}

# All global states are managed using the following dictionary.
state_dict = {
  'button_1': False, # button 1 NOT pressed
  'menu_item': 0,  # stores the index of menu_items list that is currently active
  'dark_mode': False # If True , all displays are turned off
  }

button_1_event = asyncio.Event()  # this event will be used for blocking and unblocking independent tasks as needed.
user_awaiting_button_1_response = False  # User is not waiting on button 1 response at power up.
BUTTON_1_SELECTION_WAIT_SEC = 3  # After pressing button 1 once, user will have to wait this long to confirm selection

display_modes = ['time', 'date', 'temp']
display_duration_sec = [16, 8, 8]
current_mode_idx = 0  # using display_modes[0]

dispObj = duh.display_manager(display_modes, display_modes[current_mode_idx])  # create object for managing the display states.

def I2C_scanner():
  # You can choose any other combination of I2C pins
  i2c = SoftI2C(scl=Pin(I2C_0_SCL_PIN), sda=Pin(I2C_0_SDA_PIN))

  print('I2C SCANNER')
  devices = i2c.scan()

  if len(devices) == 0:
    print("No i2c device !")
  else:
    print('i2c devices found:', len(devices))

    for device in devices:
      print("I2C hexadecimal address: ", hex(device))

################################################################

def read_temperature(display=False):
  adc_value = PI_PICO_TEMP_SENSOR.read_u16()  # 16 bit ADC used for sampling
  voltage = adc_value * (3.3 / 65535)
  temp_celcius = 27 - (voltage - 0.706) / 0.001721

  temp_fahrenheit = temp_celcius * (9/5) + 32

  if display:
    print(f"Current temperature {temp_celcius:.00f} degC or {temp_fahrenheit:.00f} F")

  return temp_celcius, temp_fahrenheit

def get_temp_list(temp_celcius, temp_fahrenheit):
  degC_list = []
  F_list = []

  MSD, LSD = divmod(int(temp_celcius), 10)
  degC_list.append(LSD)
  degC_list.append(MSD)

  MSD, LSD = divmod(int(temp_fahrenheit), 10)
  F_list.append(LSD)
  F_list.append(MSD)

  return degC_list, F_list

async def display_all_information(oledObj, rtcObj):

  while True:
    await button_1_event.wait()  # Blocked until the button 1 event is cleared

    if display_modes[current_mode_idx] == 'time':
      mode = 'time'
      delay_ms = 50  # time changes every second
    elif display_modes[current_mode_idx] == 'date':
      mode = 'date'
      delay_ms = 500  # date will not change often
    else:
      mode = 'temp'  # temperature not implemented yet
      #temp_celcius, temp_fahrenheit = read_temperature()  # this works and gets temperature from Pi Pico but it is higher than true room temperature !
      temp_celcius, temp_fahrenheit = rtcObj.get_temperature()  # this reads the temperature from the RTC and is a bit more accurate.
      delay_ms = 500  # temperature will not change often

    if not state_dict['dark_mode']:
        # Screens are ON. Continue with visualizations.
      if mode == 'temp':
        degC_list, F_list = get_temp_list(temp_celcius, temp_fahrenheit)  # low indices in the lists gives the low significant digits

        values_to_display = [images.special_symbol_codes['degC'], # display 0
                             degC_list[0], # display 1
                             degC_list[1], # display 2
                             99, # display 3 (will always be blank)
                             99, # display 4 (will always be blank)
                             images.special_symbol_codes['degF'], # display 5
                             F_list[0], # display 6
                             F_list[1], # display 7
                             ] # index of the list corresponds to the physical display index !

        update_tuples_list = dispObj.update_new(mode, values_to_display)

        for each_tuple in update_tuples_list:
          if each_tuple[0] != 3 and each_tuple[0] != 4:
            # Displays 3 and 4 will ALWAYS be blank in this mode! (see clear_display() below)
            oledObj.display_digit(each_tuple[0], each_tuple[1])  # (display idx, value to display)

        # The middle 2 displays will always be blank in temp mode.
        oledObj.clear_display(4)
        oledObj.clear_display(3)
        
      else:
        time_list = rtcObj.get_time_list(mode=mode) # Reads current time and returns MM:DD:YY or HH:MM:SS (with relevant delimiter codes).

        update_tuples_list = dispObj.update_new(mode, time_list)

        for each_tuple in update_tuples_list:
            oledObj.display_digit(each_tuple[0], each_tuple[1])  # (display idx, value to display)
         
    await asyncio.sleep_ms(delay_ms)

async def display_mode_toggle():
  global current_mode_idx  # declare global ONLY WHEN MODIFYING a variable in a task !

  while True:
    
    await button_1_event.wait()  # Blocked until the button 1 event is cleared
 
    await asyncio.sleep(display_duration_sec[current_mode_idx])  # Each information page will be displayed as per user preferences in display_duration_sec[]
    current_mode_idx = (current_mode_idx + 1) % len(display_modes)

async def button_1_menu_timeout(oledObj, rtcObj):
  global user_awaiting_button_1_response

  while True:
    if user_awaiting_button_1_response:
      cur_selected_item = menu_items[state_dict['menu_item']]  # we will check this again after button timeout
      await asyncio.sleep(BUTTON_1_SELECTION_WAIT_SEC)  # wait to observe button inactivity to confirm user selection of cur_selected_item

      if cur_selected_item == menu_items[state_dict['menu_item']]:
        # User did not press the button to change still. Menu selection confirmed.
        if cur_selected_item == "RESET_TIME_OVER_WIFI":
          mh.display_notification(oledObj, notification_messages['rtc_update'])

          status = mh.update_local_pi_time_over_wifi(wifi_credents)  # update Pi local time over WiFi first
          mh.update_rtc_time(rtcObj)  # RTC update will read Pi local time to be updated.

          if not status:
            mh.display_notification(oledObj, notification_messages['retry_update'])
            time.sleep(1)  # 1 second delay to let user read the message

        elif cur_selected_item == 'GO TO_DARK_MODE':
          state_dict['dark_mode'] = True  # all screens will be off
          oledObj.clear_all_displays()
        elif cur_selected_item == 'LET_THERE_BE_LIGHT !':
          state_dict['dark_mode'] = False  # all screens will be on   

        user_awaiting_button_1_response = False  # button request now served      
        button_1_event.set()  # all independent tasks blocked are now unblocked to resume normal operation
      
      # else user changed mind again. Continue to above conditional to restart timer.

    await asyncio.sleep_ms(50)  # no matter the outcome, come back and continue a bit later.

async def button_1_state_manager(button):
  while True:
    if button.value() == 1: # button is pressed
      if not state_dict['button_1']:
        # Button state is registered as NOT pressed. State needs to change.
        await asyncio.sleep_ms(DEBOUNCE_DELAY_MS)
        # Register button 1 state change as pressed.
        state_dict['button_1'] = True # indicates button is pressed
      #else no need to change the button state yet.
    else:
      if state_dict['button_1']:
        # Safety check in case the button press is not detected by other tasks to service the request. State needs to change.
        # Button is now released but state is still ON (i.e., a task has not serviced the request yet!)
        await asyncio.sleep_ms(DEBOUNCE_DELAY_MS)  # wait for release action to settle first
        state_dict['button_1'] = False # indicates button is released
      #else take no action.
    await asyncio.sleep_ms(50)  # no matter the outcome, come back and continue a bit later.

async def button_monitor(oledObj):
  global user_awaiting_button_1_response

  while True:
    if state_dict['button_1']:
      # User button 1 press confirmed.
      state_dict['button_1'] = False

      button_1_event.clear()  # Block all independent tasks related to display update for now
      
      state_dict['menu_item'] = (state_dict['menu_item'] + 1 ) % len(menu_items)  # circles around all menu_items with each button press
      user_awaiting_button_1_response = True

      message_words = menu_items[state_dict['menu_item']].split('_')  # words to display in each menu item can be different

      # Clear all displays first
      oledObj.clear_all_displays()

      for idx, each_word in enumerate(message_words):
        # Display one word per OLEd siapley alwyas starting from the left! (i.e. display 7 first)
        oledObj.write_scaled_text(7-idx, each_word, x=0, y=0, scale_xy=(2,3), rotate=True, y_start = 28)
      
    await asyncio.sleep_ms(100)  # no matter the outcome, come back and continue a bit later.


async def main():
  global wifi_credents

  # Configure IO pins
  button_1 = machine.Pin(BUTTON_1_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)

  # Following initializes all 8 displays
  oledObj = oled.ssd1306_i2c(I2C_MUX_ADDRESS, FIXED_SCREEN_ADDRESS, I2C_0_SCL_PIN, I2C_0_SDA_PIN)

  # Following initializes the RTC
  rtcObj = uh.RTC(DS3231_RTC_ADDRESS, I2C_0_SCL_PIN, I2C_0_SDA_PIN)

  # Following initializes the SD CARD
  sdcardObj = sdh.sdcard_spi(SDCARD_PORT_CONFIG)
  # Next, read the WiFi credentials from SDCard into memory.
  wifi_credents['ssid'], wifi_credents['password'] = sdcardObj.readWiFiCredentials("wifi_credentials.txt")

  button_1_event.set()  # All independent tasks can run now

  # Create all async tasks next
  await asyncio.gather(
    display_all_information(oledObj, rtcObj),
    display_mode_toggle(),
    button_1_state_manager(button_1),
    button_1_menu_timeout(oledObj, rtcObj),
    button_monitor(oledObj)
    )

# Run the event loop
loop = asyncio.new_event_loop()
loop.run_until_complete(main())  # Start the async tasks
loop.run_forever()  # Keep running forever

################################################################

"""
  # Scan I2C bus to retreive all connected i2c device addresses
  I2C_scanner()

  # Query device memory and file system stuff when needed.
  memObj = sm.sysman()
  memObj.report_memory_stats()
  memObj.list_modules_on_device()
  memObj.available_micropython_modules()
  """
