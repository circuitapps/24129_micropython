
import gc
import os


class sysman:

    def __init__(self):
        self.free_unused_RAM()  # free up unused RAM

    def free_unused_RAM(self):
        gc.collect()  # free up unused RAM

    def get_used_RAM(self):
        # in bytes
        return gc.mem_alloc()

    def get_free_RAM(self):
        # in bytes
        return gc.mem_free()
    
    def get_total_RAM(self):
        # in bytes
        return self.get_used_RAM() + self.get_free_RAM()

    def refresh_filesystem_stats(self):
        _fs_stat = os.statvfs("/")  # Get filesystem stats
        _block_size = _fs_stat[0]  # Get block size
        _total_blocks = _fs_stat[2]  # Get total number of blocks
        _free_blocks = _fs_stat[3]  # Get free blocks available
        
        return _block_size, _free_blocks, _total_blocks

    def get_used_flash(self):
        # in bytes
        _block_size, _free_blocks, _total_blocks = self.refresh_filesystem_stats()
        return _block_size * (_total_blocks - _free_blocks)

    def get_free_flash(self):
        # in bytes
        _block_size , _free_blocks, _ = self.refresh_filesystem_stats()
        return _block_size * _free_blocks

    def get_total_flash(self):
        # in bytes
        _block_size, _, _total_blocks = self.refresh_filesystem_stats()
        return _block_size * _total_blocks
    
    def report_memory_stats(self):
        print(f"*** RAM STATUS ***")
        print(f"Total RAM = {self.get_total_RAM()} bytes")
        print(f"Used RAM = {self.get_used_RAM()} bytes")
        print(f"Free RAM = {self.get_free_RAM()} bytes")
        print(f"*** FLASH STATUS ***")
        print(f"Total Flash = {self.get_total_flash()} bytes")
        print(f"Used Flash = {self.get_used_flash()} bytes")
        print(f"Free Flash = {self.get_free_flash()} bytes")
        print(f"*** Micropython firmware status ***")
        print(f"{os.uname()}")

    def list_modules_on_device(self):
        print(f"*** MODULES UPLOADED ON DEVICE ***")
        print(f"{os.listdir("/")}")
        print(f"*** MODULES UNDER lib DIRECTORY ***")
        print(f"{os.listdir('/lib')}")

    def available_micropython_modules(self):
        print(f"*** AVAILABLE MICROPYTHON MODULES ON FIRMWARE ***")
        print(f"{help("modules")}")