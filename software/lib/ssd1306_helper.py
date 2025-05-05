
from machine import Pin, SoftI2C
import ssd1306  # SSD1306 OLED display library
import images
import framebuf

class ssd1306_i2c():

    def __init__(self, mux_address, display_address, scl_pin, sda_pin):
        self.SCREEN_WIDTH = 128
        self.SCREEN_HEIGHT = 64
        self.TOTAL_DISPLAYS = 8  # there are 8 physical OLED displays to control

        self.mux_addr = mux_address
        self.disp_addr = display_address
        self.i2c = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin))

        self.displays_list = []  # each list index specifies the OLED display to access
        for each_disp_idx in range(self.TOTAL_DISPLAYS):
            self._switch_to_display(each_disp_idx) # Switch to the desired OLED display first
            _temp = ssd1306.SSD1306_I2C(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.i2c, addr=self.disp_addr)
            self.displays_list.append(_temp)
            
    def _switch_to_display(self, display_idx):
        temp = bytearray(2)
        temp[0] = 0x80  # Co=1, D/C#=0
        temp[1] = (1 << display_idx)
        self.i2c.writeto(self.mux_addr, temp)  # Switch to the desired OLD display first

    def write_text(self, display_idx, text_str, x=0, y=0):
        self._switch_to_display(display_idx)
        self.displays_list[display_idx].text(text_str, x, y)
        self.displays_list[display_idx].show()


    def write_scaled_text(self, display_idx, text_str, x=0, y=0, scale_xy=(1,1), clear_display=True, rotate=False, x_start = 120, y_start = 0):
        """
        scale_xy=(1,1) has to have integer values.
        """

        # Uses FrameBuffer !
        self._switch_to_display(display_idx)
        if clear_display:
            self.clear_display(display_idx)  # erase display content first

        char_pix_width = 8  # pixels
        char_pix_height = 8  # pixels

        # First create a temp buffer to store each character in text_str line as 8 pixel x 8 pixel
        # Make sure the length of the string does not exceed the width of the OLED screen.
        PER_CHAR_SCALED_X_PIXEL_COUNT = char_pix_width * scale_xy[0]
        PER_CHAR_SCALED_Y_PIXEL_COUNT = char_pix_height * scale_xy[1]
        TEXT_STR_COL_PIXEL_COUNT = char_pix_width * len(text_str)

        if TEXT_STR_COL_PIXEL_COUNT <= self.SCREEN_WIDTH\
            and (PER_CHAR_SCALED_X_PIXEL_COUNT * len(text_str)) <= self.SCREEN_WIDTH\
            and PER_CHAR_SCALED_Y_PIXEL_COUNT <= self.SCREEN_HEIGHT:
            # Made sure the scaled text will fit the screen (if scaled text does not fit, the rotated version will always be cropped also !!!)
            # temp_fb holds the original text in memory with no scaling
            temp_fb = framebuf.FrameBuffer(bytearray(char_pix_width * len(text_str)), char_pix_width * len(text_str), char_pix_height, framebuf.MONO_VLSB)
            temp_fb.text(text_str, 0, 0)

            # fbuf will hold the scaled version of the text
            # scale in x and y directions can be different
            fbuf_scaled = framebuf.FrameBuffer(bytearray(self.SCREEN_HEIGHT * self.SCREEN_WIDTH), self.SCREEN_WIDTH, self.SCREEN_HEIGHT, framebuf.MONO_VLSB)  # Works and is simple! No need offsets for y=20+
            fbuf_rotated = framebuf.FrameBuffer(bytearray(self.SCREEN_HEIGHT * self.SCREEN_WIDTH), self.SCREEN_WIDTH, self.SCREEN_HEIGHT, framebuf.MONO_VLSB)  # Works and is simple! No need offsets for y=20+

            for char_idx in range(len(text_str)):
                
                # Following is for scaling a text character
                """
                for char_x in range(char_pix_width): # 8 pixel width of character
                    for char_y in range(char_pix_height):  # 8 pixel height of character
                        if temp_fb.pixel(char_x + (char_idx * char_pix_width), char_y):   #(each_row, each_col):
                            # not background color. Draw the scaled version of this pixel next.
                            for sx in range(scale_xy[0]):
                                for sy in range(scale_xy[1]):
                                    fbuf_scaled.pixel(
                                        x + sx + (char_x +  char_idx * char_pix_width) * scale_xy[0],
                                        y + sy + (char_y * scale_xy[1]),
                                        1
                                        )
                """

                # Following is for scaling a text character
                self.scale_character(temp_fb, fbuf_scaled, char_idx, x, y, scale_xy, char_pix_width, char_pix_height)  # Modifies fbuf_scaled

                # Following is for placing the scaled character along the centerline when the display is turned 90 deg anti-clockwise.
                _xmin = (char_idx * char_pix_width) * scale_xy[0]
                _xmax = (scale_xy[0] - 1) + ( (char_pix_width - 1) +  char_idx * char_pix_width) * scale_xy[0]
                #_ymin = 0
                _ymax = scale_xy[1] - 1 + ((char_pix_height - 1) * scale_xy[1])

                x_range = (_xmin, _xmax)  # (x min, x max) in fbuf_scaled
                y_range = (0, _ymax)  # (y min, y max) in fbuf_scaled

                x_offset = char_idx * (y_range[1] + 1 - y_range[0])
                y_offset = char_idx * (x_range[1] + 1 - x_range[0])

                self.CC90_rotate_and_center_character(fbuf_scaled, fbuf_rotated, x_range, y_range, x_offset, y_offset, x_start = x_start, y_start = y_start)  # Modifies fbuf_rotated

                """
                x_start, y_start = 127, 24  # center of the screen based on 90 deg anti-clockwise rotation of display

                for xs in range(x_range[0], x_range[1]):
                    # Iterates on fbuf_scaled x coordinates
                    for ys in range(y_range[0], y_range[1]):
                        # Iterates on fbuf_scaled y coordinates
                        if fbuf_scaled.pixel(xs, ys):
                            # Not a background pixel
                            fbuf_rotated.pixel(
                                                x_start - ys - ( char_idx * (y_range[1] + 1 - y_range[0]) ),\
                                                y_start + xs - ( char_idx * (x_range[1] + 1 - x_range[0]) ),\
                                                1
                                                )
                """

            if rotate:
                # Scaled AND roated text will be displayed
                fbuf_final = fbuf_rotated
            else:
                # Scaled text will be displayed (no rotation)
                fbuf_final = fbuf_scaled

            self.show_buffer(display_idx, fbuf_final, x, y)  # show final fbuf content on target display

        else:
            # Text does not fit the screen
            error_msg="Text too long"
            temp_fb = framebuf.FrameBuffer(bytearray(self.SCREEN_WIDTH * self.SCREEN_HEIGHT), char_pix_width * len(error_msg), char_pix_height, framebuf.MONO_VLSB)
            temp_fb.text(error_msg, 0, 0)  # Print error message
            self.show_buffer(display_idx, temp_fb)  # show framebuffer content on target display

    def scale_character(self, src_fb, dest_scaled, char_idx, x_start, y_start, scale_xy, char_pix_width, char_pix_height):
                    
                for char_x in range(char_pix_width): # 8 pixel width of character
                    for char_y in range(char_pix_height):  # 8 pixel height of character
                        if src_fb.pixel(char_x + (char_idx * char_pix_width), char_y):   #(each_row, each_col):
                            # not background color. Draw the scaled version of this pixel next.
                            for sx in range(scale_xy[0]):
                                for sy in range(scale_xy[1]):
                                    dest_scaled.pixel(
                                        x_start + sx + (char_x +  char_idx * char_pix_width) * scale_xy[0],
                                        y_start + sy + (char_y * scale_xy[1]),
                                        1
                                        )

    def CC90_rotate_and_center_character(self, source_fbuf, dest_fbuf, x_range, y_range, x_offset, y_offset, x_start = 127, y_start = 0):
        
        #x_start, y_start = 127, 0  Default position on the screen based on 90 deg anti-clockwise rotation of display

        for xs in range(x_range[0], x_range[1]):
            # Iterates on fbuf_scaled x coordinates
            for ys in range(y_range[0], y_range[1]):
                # Iterates on fbuf_scaled y coordinates
                if source_fbuf.pixel(xs, ys):
                    # Not a background pixel
                    dest_fbuf.pixel(
                                    x_start - ys - x_offset,\
                                    y_start + xs - y_offset,\
                                    1
                                    )

    def display_fill(self, display_idx, color=0):
        self._switch_to_display(display_idx)
        self.displays_list[display_idx].fill(color)
        self.displays_list[display_idx].show()

    def display_digit(self, display_idx, digit_val):
        self.clear_display(display_idx)  # switches to the display and erases its content first
        _fbuf = framebuf.FrameBuffer(images.IMAGE_MAP[digit_val], self.SCREEN_WIDTH, self.SCREEN_HEIGHT, framebuf.MONO_VLSB)
        self.show_buffer(display_idx, _fbuf)  # show framebuffer content on target display

    def clear_display(self, display_idx):
        self.display_fill(display_idx)  # erases display content

    def clear_all_displays(self):
        for each_display_idx in range(self.TOTAL_DISPLAYS):
            self.clear_display(each_display_idx)

    def show_buffer(self, display_idx, fbuf, x_offset=0, y_offset=0):
        # Use when framebuffer is used for storing content
        self.displays_list[display_idx].blit(fbuf, x_offset, y_offset)  # required since we are using OLED with ssd1306
        self.displays_list[display_idx].show()
