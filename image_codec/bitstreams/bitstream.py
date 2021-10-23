class Bitstream:
    def __init__(self, file_path: str, file_mode: str):
        self.file = open(file_path, file_mode)
        self.buffer = 0
        self.bit_counter = 0

    def align_byte(self):
        pass

    def terminate(self):
        self.align_byte()
        self.file.close()
