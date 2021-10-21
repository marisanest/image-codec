import numpy as np

from .arithmetic import ArithmeticDecoder
from ..bitstreams.input import InputBitstream
from ..block import Block
from ..context_modeler import ContextModeler
from ..modes import PartitioningMode, PredictionMode
from ..parameters import PartitioningModeParameters, PredictionModeParameters
from ..probability_model import ProbabilityModel
from ..utils import sign


class EntropyDecoder:
    def __init__(self, bitstream: InputBitstream, block_size: int):
        self.arithmetic_decoder = ArithmeticDecoder(bitstream)
        self.context_modeler = ContextModeler(block_size)

    def decode_block(self, block: Block) -> PartitioningModeParameters:
        partitioning_mode_parameters = PartitioningModeParameters(
            partitioning_mode=self.decode_partitioning_mode()
        )

        for partition in block.partitions(
            partitioning_mode_parameters.partitioning_mode
        ):
            prediction_mode_parameters = PredictionModeParameters(
                prediction_mode=self.decode_prediction_mode()
            )
            partition.q_indexes = self.decode_q_indexes(partition.block_size)
            prediction_mode_parameters.block = partition
            partitioning_mode_parameters.merge(prediction_mode_parameters)

        return partitioning_mode_parameters

    def decode_q_indexes(self, block_size: int) -> np.array:
        q_indexes_block = np.zeros(block_size * block_size, dtype=np.int32)

        if not self.arithmetic_decoder.decode_bit(
            self.context_modeler.probability_codeblock_flag
        ):
            return q_indexes_block.reshape([block_size, block_size]).reshape(
                block_size, block_size
            )

        last_scan_index = self.exp_golomb_prob_adapted(
            self.context_modeler.probability_last_prefix
        )
        assert last_scan_index >= 0
        assert last_scan_index < int(block_size * block_size)

        q_indexes_block[last_scan_index] = self.decode_q_index(
            last_scan_index, is_last=True
        )
        for index in range(last_scan_index - 1, -1, -1):
            q_indexes_block[index] = self.decode_q_index(index)

        # todo
        return q_indexes_block.reshape([block_size, block_size]).reshape(
            block_size, block_size
        )

    def decode_q_index(self, index: int, is_last=False) -> int:
        self.context_modeler.switch_context(index)

        if not is_last:
            if (
                self.arithmetic_decoder.decode_bit(
                    self.context_modeler.probability_signal_flag
                )
                == 0
            ):
                return 0

        if (
            self.arithmetic_decoder.decode_bit(
                self.context_modeler.probability_gt1_flag
            )
            == 0
        ):
            return sign(self.arithmetic_decoder.decode_bit_bypass())

        q_index = (
            self.exp_golomb_prob_adapted(self.context_modeler.probability_level_prefix)
            + 2
        )
        q_index *= sign(self.arithmetic_decoder.decode_bit_bypass())

        return q_index

    def decode_partitioning_mode(self) -> PartitioningMode:
        return (
            PartitioningMode.NON_SUB_PARTITIONING
            if self.arithmetic_decoder.decode_bit(
                self.context_modeler.partitioning_mode_bit
            )
            == 0
            else PartitioningMode.SUB_PARTITIONING
        )

    def decode_prediction_mode(self) -> PredictionMode:
        if (
            self.arithmetic_decoder.decode_bit(
                self.context_modeler.prediction_mode_bit1
            )
            == 0
        ):
            return PredictionMode.PLANAR_PREDICTION
        elif (
            self.arithmetic_decoder.decode_bit(
                self.context_modeler.prediction_mode_bit2
            )
            == 0
        ):
            return PredictionMode.DC_PREDICTION
        elif (
            self.arithmetic_decoder.decode_bit(
                self.context_modeler.prediction_mode_bit3
            )
            == 0
        ):
            return PredictionMode.HORIZONTAL_PREDICTION
        else:
            return PredictionMode.VERTICAL_PREDICTION

    def exp_golomb_prob_adapted(self, probability_model: ProbabilityModel) -> int:
        length = 0

        while not self.arithmetic_decoder.decode_bit(probability_model):
            length += 1

        value = 1
        if length > 0:
            value = value << length
            value += self.arithmetic_decoder.decode_bits_bypass(length)

        value -= 1

        return value

    def terminate(self):
        self.arithmetic_decoder.terminate()
