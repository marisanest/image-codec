import numpy as np

from dataclasses import dataclass, field
from typing import List, Union

from .bitstreams.input import InputBitstream
from .bitstreams.output import OutputBitstream
from .block import Block
from .frame import Frame
from .modes import PredictionMode, PartitioningMode


@dataclass
class Parameters:
    cost: float = 0


@dataclass
class PredictionModeParameters(Parameters):
    prediction_mode: PredictionMode = None
    block: Block = None


@dataclass
class PartitioningModeParameters(Parameters):
    partitioning_mode: PartitioningMode = None
    prediction_mode_parameters_list: List[PredictionModeParameters] = field(
        default_factory=list
    )

    def merge(self, prediction_mode_parameters: PredictionModeParameters):
        self.cost += prediction_mode_parameters.cost
        self.prediction_mode_parameters_list.append(prediction_mode_parameters)


class ParametersList:
    def __init__(self):
        self.parameters_list = []

    def append(self, parameters: Parameters):
        self.parameters_list.append(parameters)

    def optimal(
        self,
    ) -> Union[Parameters, PredictionModeParameters, PartitioningModeParameters]:
        return min(self.parameters_list, key=lambda parameters: parameters.cost)

    def __len__(self) -> int:
        return len(self.parameters_list)


@dataclass
class MetaParameters:

    N_BITS_HEIGHT = 16
    N_BITS_WIDTH = 16
    N_BITS_BLOCK_SIZE = 16
    N_BITS_QUALITY_PARAMETER = 8

    def __init__(
        self, height: int, width: int, block_size: int, quality_parameter: int
    ):
        self.height = height
        self.width = width
        self.block_size = block_size
        self.quality_parameter = quality_parameter
        self.quantization_step_size: float = 2 ** (self.quality_parameter / 4)
        self.lagrange_multiplier: float = (
            self.quantization_step_size * self.quantization_step_size
        )

    def encode(self, output_bitstream: OutputBitstream):
        output_bitstream.write_bits(self.height, self.N_BITS_HEIGHT)
        output_bitstream.write_bits(self.width, self.N_BITS_WIDTH)
        output_bitstream.write_bits(self.block_size, self.N_BITS_BLOCK_SIZE)
        output_bitstream.write_bits(
            self.quality_parameter, self.N_BITS_QUALITY_PARAMETER
        )

    @classmethod
    def decode(cls, input_bitstream: InputBitstream) -> 'parameters.MetaParameters':
        return cls(
            height=input_bitstream.read_bits(cls.N_BITS_HEIGHT),
            width=input_bitstream.read_bits(cls.N_BITS_WIDTH),
            block_size=input_bitstream.read_bits(cls.N_BITS_BLOCK_SIZE),
            quality_parameter=input_bitstream.read_bits(cls.N_BITS_QUALITY_PARAMETER),
        )

    def build_frame(self) -> Frame:
        return Frame(
            np.zeros([self.height, self.width], dtype=np.uint8), self.block_size
        )
