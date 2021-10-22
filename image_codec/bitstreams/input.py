from .bitstream import Bitstream


class InputBitstream(Bitstream):
    def __init__(self, input_path: str):
        super().__init__(input_path)

    def read_bit(self) -> int:
        if self.bit_counter == 0:
            byte_s = self.file.read(1)
            self._validate_bytes(byte_s)
            self.buffer = byte_s[0]
            self.bit_counter = 8

        self.bit_counter -= 1

        return (self.buffer >> self.bit_counter) & 1

    def read_bits(self, n_bits: int) -> int:
        if n_bits <= self.bit_counter:
            self.bit_counter -= n_bits
            return (self.buffer >> self.bit_counter) & ((1 << n_bits) - 1)

        bit_pattern = 0

        if self.bit_counter != 0:
            bit_pattern = self.buffer & ((1 << self.bit_counter) - 1)
            n_bits -= self.bit_counter
            self.bit_counter = 0

        while n_bits >= 8:
            byte_s = self.file.read(1)
            self._validate_bytes(byte_s)
            bit_pattern = (bit_pattern << 8) | int(byte_s[0])
            n_bits -= 8

        if n_bits > 0:
            byte_s = self.file.read(1)
            self._validate_bytes(byte_s)
            self.buffer = byte_s[0]
            self.bit_counter = 8 - n_bits
            bit_pattern = (bit_pattern << n_bits) | (self.buffer >> self.bit_counter)

        return bit_pattern

    def align_byte(self):
        self.bit_counter = 0

    @staticmethod
    def _validate_bytes(byte_s: bytes):
        if not byte_s:
            raise Exception('InputBitstream: Tried to read byte after eof.')
