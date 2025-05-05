
class display_manager():

    def __init__(self, display_modes, active_display_mode):
        
        self.active_display_mode = active_display_mode  # for managing how to update the displays

        self.update_buffer = {}
        for each_key in display_modes:
            self.update_buffer[each_key] = {'old': [], 'new': []}
            self.init_dict(each_key)  # each dictionary will have a specific update

    def init_dict(self, display_mode_key):
        self.update_buffer[display_mode_key]['old'] = [99] * 8  # 8 invalid numbers to ensure display update at the start
        self.update_buffer[display_mode_key]['new'] = [99] * 8  # 8 invalid numbers to ensure display update at the start

    def clone_new_to_old(self, display_mode_key):
        self.update_buffer[display_mode_key]['old'] = self.update_buffer[display_mode_key]['new'][:]  # slice COPYING list content

    def get_update_tuples(self, display_mode_key):
         # A list of tuples will be returned where the first tuple value will be the display number to update
         # The second tuple value will be the IMAGE_MAP key value to use for displaying the required image.
        
        lot = []  # list of tuples

        for display_idx, value in enumerate(self.update_buffer[display_mode_key]['new']):
            if value != self.update_buffer[display_mode_key]['old'][display_idx]:
                # display needs to be updated as values do not match
                lot.append((display_idx, value))
            #else value has not changed. No update needed for this display.
        
        return lot

    def update_new(self, display_mode_key, values_to_display):

        self.update_buffer[display_mode_key]['new'] = values_to_display[:]  # Copy values read from hardware (for each display) into new buffer

        if self.active_display_mode == display_mode_key:
            # A FIRST update has already been performed in this display mode. Update ONLY IF values have changed since the last update!
            update_tuples = self.get_update_tuples(display_mode_key)  # get which displays need to be refreshed with which value for the caller
            self.clone_new_to_old(display_mode_key)  # internal update for next round
        else:
            # Mode has changed since last update. A FIRST display update needs to be performed now.
            self.active_display_mode = display_mode_key  # Keep track of this mode change internally
            update_tuples = []
            # Following will force ALL DISPLAYS to update by the caller.
            for display_idx, value in enumerate(values_to_display):
                update_tuples.append((display_idx, value))

        return update_tuples
