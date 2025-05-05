
from machine import SPI, Pin
import sdcard, os

class sdcard_spi():

    def __init__(self, sd_card_port_config):
        self.SPI_BUS = sd_card_port_config['SPI_BUS']
        self.SCK_PIN = sd_card_port_config['SCK_PIN']
        self.MOSI_PIN = sd_card_port_config['MOSI_PIN']
        self.MISO_PIN = sd_card_port_config['MISO_PIN']
        self.CS_PIN = sd_card_port_config['CS_PIN']
        self.SD_MOUNT_PATH = '/sd'

        try:
            # Init SPI communication
            self.spi = SPI(self.SPI_BUS,sck=Pin(self.SCK_PIN), mosi=Pin(self.MOSI_PIN), miso=Pin(self.MISO_PIN))
            self.cs = Pin(self.CS_PIN)
            self.sd = sdcard.SDCard(self.spi, self.cs)
            # Mount microSD card
            os.mount(self.sd, self.SD_MOUNT_PATH)
            # List files on the microSD card
            #print(os.listdir(self.SD_MOUNT_PATH))
    
        except Exception as e:
            print('An error occurred:', e)

    def create_file(self, filename):
        __file_path = f"{self.SD_MOUNT_PATH}/{filename}"

        with open(__file_path, "w") as __file:
            __file.write("Hello new file!\n")

    def read_file(self, filename):
        __file_path = f"{self.SD_MOUNT_PATH}/{filename}"

        with open(__file_path, "r") as __file:
            __content=__file.read()
        
        return __content

    def readWiFiCredentials(self, credentials_filename):
        __filecontent = self.read_file(credentials_filename)

        lines = __filecontent.split('\n')  # lines[0] will have the ssid info, lines[1] will have the password information. The rest (if any) can be ignored.
        ssid = lines[0].split(':')[-1].strip()  # white space characters around the ssid are also removed
        password=lines[1].split(':')[-1].strip()  # white space characters around the password are also removed
        
        return ssid, password