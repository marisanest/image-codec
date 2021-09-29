from ..bitstreams.output import OutputBitstream
from ..probability_model import ProbabilityModel


class ArithmeticEncoder:

    def __init__(self, output_bitstream: OutputBitstream):
        self.output_bitstream = output_bitstream
        self.output_bitstream.byte_align()
        self.low: int = 0
        self.range: int = 510
        self.buffered_byte: int = 255
        self.n_buffered_bytes: int = 0
        self.bits_left: int = 23

    def encode_bit(self, bit: int, probability_model: ProbabilityModel):
        lps: int = ProbabilityModel.LPS_TABLE[probability_model.state()][(self.range >> 6) & 3]
        self.range -= lps
        
        if bit != probability_model.mps():
            n_bits: int = ProbabilityModel.RENORM_TABLE[lps >> 3]
            self.low = (self.low + self.range) << n_bits
            self.range = lps << n_bits
            self.bits_left -= n_bits
            self.test_and_write_out()
            probability_model.update_lps()
        else:
            if self.range < 256:
                self.low <<= 1
                self.range <<= 1
                self.bits_left -= 1
                self.test_and_write_out()
            
            probability_model.update_mps()

    def encode_bits(self, bit_pattern: int, n_bits: int, probability_model: ProbabilityModel):
        while n_bits > 0:
            n_bits -= 1
            self.encode_bit((bit_pattern >> n_bits) & 1, probability_model)

    def encode_bit_bypass(self, bit: int):
        self.low <<= 1
        if bit:
            self.low += self.range
        self.bits_left -= 1
        self.test_and_write_out()

    def encode_bits_bypass(self, bit_pattern: int, n_bits: int):
        while n_bits > 8:
            n_bits -= 8
            sub_bit_pattern = (bit_pattern >> n_bits) & 255
            self.low = (self.low << 8) + int(self.range * sub_bit_pattern)
            self.bits_left -= 8
            self.test_and_write_out()
        
        sub_bit_pattern = bit_pattern & ((1 << n_bits) - 1)
        self.low = (self.low << n_bits) + int(self.range * sub_bit_pattern)
        self.bits_left -= n_bits
        self.test_and_write_out()

    def test_and_write_out(self):
        if self.bits_left < 12:
            lead_byte: int = self.low >> (24 - self.bits_left)
            self.bits_left += 8
            self.low &= (4294967295 >> self.bits_left)

            if lead_byte == 255:
                self.n_buffered_bytes += 1
            else:
                if self.n_buffered_bytes > 0:
                    carry: int = lead_byte >> 8
                    byte: int = self.buffered_byte + carry
                    self.buffered_byte = lead_byte & 255
                    self.output_bitstream.write_bits(byte, 8)
                    byte = (255 + carry) & 255

                    while self.n_buffered_bytes > 1:
                        self.output_bitstream.write_bits(byte, 8)
                        self.n_buffered_bytes -= 1
                else:
                    self.n_buffered_bytes = 1
                    self.buffered_byte = lead_byte

    def terminate(self):
        self.range -= 2
        self.low += self.range
        self.low <<= 7
        self.range = 2 << 7
        self.bits_left -= 7
        self.test_and_write_out()
        
        if (self.low >> (32 - self.bits_left)) > 0:
            self.output_bitstream.write_bits(self.buffered_byte + 1, 8)
            
            while self.n_buffered_bytes > 1:
                self.output_bitstream.write_bits(0, 8)
                self.n_buffered_bytes -= 1
                
            self.low -= (1 << (32 - self.bits_left))
        else:
            if self.n_buffered_bytes > 0:
                self.output_bitstream.write_bits(self.buffered_byte, 8)
            
            while self.n_buffered_bytes > 1:
                self.output_bitstream.write_bits(255, 8)
                self.n_buffered_bytes -= 1
        
        self.output_bitstream.write_bits(self.low >> 8, 24 - self.bits_left)
        self.output_bitstream.write_bit(1)
        self.output_bitstream.byte_align()
