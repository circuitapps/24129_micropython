import wifi_conn as wicon

def update_local_pi_time_over_wifi(wifi_credents, print_time=False):
    wifiObj = wicon.wifi()
    #wifiObj.wifi_scan()  # to see WiFi networks around
    status = wifiObj.wifi_connect(wifi_credents['password'], wifi_credents['ssid'])

    if status:
        # If WiFi connection is successful, local time will be updated.
        wifiObj.update_pi_localtime()
        wifiObj.disconnect_wifi()  # close WiFi connection as it is not needed anymore.

        if print_time: # optional
            wifiObj.get_pi_localtime()  # reports the updated time for sanity check

    return status

def update_rtc_time(rtcObj, print_time=False):
    rtcObj.update_RTC()
    
    if print_time:  # Optional
        rtcObj.get_RTC_time()

def display_notification(oledObj, message_text):
    _msg_words = message_text.split('_')  # split all words of the message first
    for idx, each_word in enumerate(_msg_words):
    # Display one word per OLED screen always starting from the left! (i.e. display 7 first)
        oledObj.write_scaled_text(7-idx, each_word, x=0, y=0, scale_xy=(2,3), rotate=True, y_start = 28)