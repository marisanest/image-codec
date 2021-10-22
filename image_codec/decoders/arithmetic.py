from ..bitstreams.input import InputBitstream
from ..probability_model import ProbabilityModel


class ArithmeticDecoder:
    def __init__(self, bitstream: InputBitstream):
        self.bitstream = bitstream
        self.bitstream.align_byte()
        self.bit_pattern: int = self.bitstream.read_bits(16)
        self.bits_needed: int = -8
        self.range: int = 510

    def decode_bit(self, probability_model: ProbabilityModel) -> int:
        bit: int = probability_model.mps()
        lps: int = ProbabilityModel.LPS_TABLE[probability_model.state()][
            (self.range >> 6) - 4
        ]

        self.range -= lps
        scaled_range: int = self.range << 7

        if self.bit_pattern < scaled_range:

            if scaled_range < (256 << 7):
                self.range = scaled_range >> 6
                self.bit_pattern += self.bit_pattern
                self.bits_needed += 1

                if self.bits_needed == 0:
                    self.bits_needed = -8
                    self.bit_pattern += self.bitstream.read_bits(8)

            probability_model.update_mps()
        else:
            bit = 1 - bit
            n_bits: int = ProbabilityModel.RE_NORM_TABLE[lps >> 3]
            self.bit_pattern = (self.bit_pattern - scaled_range) << n_bits
            self.range = lps << n_bits
            self.bits_needed += n_bits

            if self.bits_needed >= 0:
                self.bit_pattern += self.bitstream.read_bits(8) << self.bits_needed
                self.bits_needed -= 8

            probability_model.update_lps()

        return bit

    def decode_bits(self, n_bits: int, probability_model: ProbabilityModel) -> int:
        value: int = 0
        while n_bits:
            n_bits -= 1
            value = (value << 1) | self.decode_bit(probability_model)
        return value

    def decode_bit_bypass(self) -> int:
        self.bit_pattern += self.bit_pattern
        self.bits_needed += 1

        if self.bits_needed >= 0:
            self.bits_needed = -8
            self.bit_pattern += self.bitstream.read_bits(8)

        scaled_range: int = self.range << 7

        if self.bit_pattern >= scaled_range:
            self.bit_pattern -= scaled_range
            return 1

        return 0

    def decode_bits_bypass(self, n_bits: int) -> int:
        value: int = 0

        while n_bits > 8:
            self.bit_pattern <<= 8
            self.bit_pattern += int(
                self.bitstream.read_bits(8) << (8 + self.bits_needed)
            )
            scaled_range: int = self.range << 15
            for i in range(8):
                value += value
                scaled_range >>= 1

                if self.bit_pattern >= scaled_range:
                    value += 1
                    self.bit_pattern -= scaled_range
            n_bits -= 8

        self.bits_needed += n_bits
        self.bit_pattern <<= n_bits

        if self.bits_needed >= 0:
            self.bit_pattern += int(self.bitstream.read_bits(8) << self.bits_needed)
            self.bits_needed -= 8

        scaled_range: int = self.range << (n_bits + 7)

        for i in range(n_bits):
            value += value
            scaled_range >>= 1
            if self.bit_pattern >= scaled_range:
                value += 1
                self.bit_pattern -= scaled_range

        return value

    def terminate(self):
        self.range -= 2
        scaled_range: int = self.range << 7

        if self.bit_pattern < scaled_range:
            raise Exception(
                "Arithmetic codeword not correctly terminated at end of frame"
            )
