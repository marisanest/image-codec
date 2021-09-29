class OutputBitstream:

    def __init__(self, filename):
        self.file = open(filename, 'wb')
        self.buffer = 0
        self.bit_counter = 0

    def write_bit(self, bit: int):
        self.buffer = (self.buffer << 1) | int(bool(bit))
        self.bit_counter += 1
        if self.bit_counter == 8:
            self.file.write(self.buffer.to_bytes(1, byteorder='big'))
            self.buffer = 0
            self.bit_counter = 0

    def write_bits(self, bit_pattern: int, n_bits: int):
        if self.bit_counter + n_bits < 8:
            self.buffer = (self.buffer << n_bits) | int(bit_pattern & ((1 << n_bits) - 1))
            self.bit_counter += n_bits
            return
        if self.bit_counter:
            free_bits = 8 - self.bit_counter
            self.buffer = (self.buffer << free_bits) | int((bit_pattern >> (n_bits - free_bits)) & ((1 << free_bits) - 1))
            n_bits -= free_bits
            self.file.write(self.buffer.to_bytes(1, byteorder='big'))
        while n_bits >= 8:
            n_bits -= 8
            self.buffer = int(bit_pattern >> n_bits) & 255
            self.file.write(self.buffer.to_bytes(1, byteorder='big'))
        self.buffer = int(bit_pattern & ((1 << n_bits) - 1))
        self.bit_counter = n_bits

    def byte_align(self):
        if self.bit_counter != 0:
            self.write_bits(0, 8 - self.bit_counter)

    def terminate(self):
        self.byte_align()
        self.file.close()
