import numpy as np
import copy

from .arithmetic import ArithmeticEncoder
from ..bitstreams.output import OutputBitstream
from ..context_modeler import ContextModeler
from ..block import Block
from ..modes import PartitioningMode, PredictionMode
from ..parameters import PartitioningModeParameters
from ..utils import count_bits


class EntropyEncoder:
    def __init__(self, output_bitstream: OutputBitstream, block_size: int):
        self.arithmetic_encoder = ArithmeticEncoder(output_bitstream)
        self.context_modeler = ContextModeler(block_size)
        self.estimated_bits = 0

    def encode_block(self, parameters: PartitioningModeParameters):
        self.encode_partitioning_mode(parameters.partitioning_mode)
        for prediction_mode_parameters in parameters.prediction_mode_parameters_list:
            self.encode_prediction_mode(prediction_mode_parameters.prediction_mode)
            self.encode_q_indexes(prediction_mode_parameters.block)

    def encode_q_indexes(self, block: Block):
        q_indexes_block = block.q_indexes.ravel()

        coded_block_flag = np.any(q_indexes_block != 0)
        self.arithmetic_encoder.encode_bit(
            coded_block_flag, self.context_modeler.probability_codeblock_flag
        )
        if not coded_block_flag:
            return

        last_scan_index = np.max(np.nonzero(q_indexes_block))
        assert last_scan_index >= 0
        assert last_scan_index < int(block.block_size * block.block_size)

        self.exp_golomb_prob_adapted(
            last_scan_index, self.context_modeler.probability_last_prefix
        )
        self.encode_q_index(
            q_indexes_block[last_scan_index], last_scan_index, is_last=True
        )
        for index in range(last_scan_index - 1, -1, -1):
            self.encode_q_index(q_indexes_block[index], index)

    def encode_q_index(self, q_index: int, index: int, is_last: bool = False):
        self.context_modeler.switch_context(index)

        if q_index == 0:
            self.arithmetic_encoder.encode_bit(
                0, self.context_modeler.probability_signal_flag
            )
            return
        elif abs(q_index) == 1:
            if not is_last:
                self.arithmetic_encoder.encode_bit(
                    1, self.context_modeler.probability_signal_flag
                )
            self.arithmetic_encoder.encode_bit(
                0, self.context_modeler.probability_gt1_flag
            )
            self.arithmetic_encoder.encode_bit_bypass(q_index > 0)
            return

        if not is_last:
            self.arithmetic_encoder.encode_bit(
                1, self.context_modeler.probability_signal_flag
            )

        self.arithmetic_encoder.encode_bit(1, self.context_modeler.probability_gt1_flag)
        self.exp_golomb_prob_adapted(
            abs(q_index) - 2, self.context_modeler.probability_level_prefix
        )
        self.arithmetic_encoder.encode_bit_bypass(q_index > 0)

    def encode_partitioning_mode(self, partitioning_mode: PartitioningMode):
        if partitioning_mode == PartitioningMode.NON_SUB_PARTITIONING:
            self.arithmetic_encoder.encode_bit(
                0, self.context_modeler.partitioning_mode_bit
            )
        else:
            self.arithmetic_encoder.encode_bit(
                1, self.context_modeler.partitioning_mode_bit
            )

    def encode_prediction_mode(self, prediction_mode: PredictionMode):
        if prediction_mode == PredictionMode.PLANAR_PREDICTION:
            self.arithmetic_encoder.encode_bit(
                0, self.context_modeler.prediction_mode_bit1
            )
        elif prediction_mode == PredictionMode.DC_PREDICTION:
            self.arithmetic_encoder.encode_bit(
                1, self.context_modeler.prediction_mode_bit1
            )
            self.arithmetic_encoder.encode_bit(
                0, self.context_modeler.prediction_mode_bit2
            )
        elif prediction_mode == PredictionMode.HORIZONTAL_PREDICTION:
            self.arithmetic_encoder.encode_bit(
                1, self.context_modeler.prediction_mode_bit1
            )
            self.arithmetic_encoder.encode_bit(
                1, self.context_modeler.prediction_mode_bit2
            )
            self.arithmetic_encoder.encode_bit(
                0, self.context_modeler.prediction_mode_bit3
            )
        else:
            self.arithmetic_encoder.encode_bit(
                1, self.context_modeler.prediction_mode_bit1
            )
            self.arithmetic_encoder.encode_bit(
                1, self.context_modeler.prediction_mode_bit2
            )
            self.arithmetic_encoder.encode_bit(
                1, self.context_modeler.prediction_mode_bit3
            )

    def estimate_block_bits(
        self,
        block: Block,
        partitioning_mode: PartitioningMode,
        prediction_mode: PredictionMode,
        is_first_partition: bool = True,
    ) -> int:
        self.estimated_bits = 0
        original_context_modeler = copy.deepcopy(self.context_modeler)

        if partitioning_mode == PartitioningMode.NON_SUB_PARTITIONING:
            self.estimated_bits += (
                self.context_modeler.partitioning_mode_bit.estimate_bits(0)
            )
        elif (
            partitioning_mode == PartitioningMode.SUB_PARTITIONING
            and is_first_partition
        ):
            self.estimated_bits += (
                self.context_modeler.partitioning_mode_bit.estimate_bits(1)
            )

        if prediction_mode == PredictionMode.PLANAR_PREDICTION:
            self.estimated_bits += (
                self.context_modeler.prediction_mode_bit1.estimate_bits(0)
            )
        elif prediction_mode == PredictionMode.DC_PREDICTION:
            self.estimated_bits += (
                self.context_modeler.prediction_mode_bit1.estimate_bits(1)
            )
            self.estimated_bits += (
                self.context_modeler.prediction_mode_bit2.estimate_bits(0)
            )
        elif prediction_mode == PredictionMode.HORIZONTAL_PREDICTION:
            self.estimated_bits += (
                self.context_modeler.prediction_mode_bit1.estimate_bits(1)
            )
            self.estimated_bits += (
                self.context_modeler.prediction_mode_bit2.estimate_bits(1)
            )
            self.estimated_bits += (
                self.context_modeler.prediction_mode_bit3.estimate_bits(0)
            )
        else:
            self.estimated_bits += (
                self.context_modeler.prediction_mode_bit1.estimate_bits(1)
            )
            self.estimated_bits += (
                self.context_modeler.prediction_mode_bit2.estimate_bits(1)
            )
            self.estimated_bits += (
                self.context_modeler.prediction_mode_bit3.estimate_bits(1)
            )

        self.estimate_q_indexes_bits(block.q_indexes)
        self.context_modeler = original_context_modeler

        return self.estimated_bits

    def estimate_q_indexes_bits(self, q_indexes: np.array):
        q_indexes = q_indexes.ravel()

        coded_block_flag = np.any(q_indexes != 0)
        self.estimated_bits += (
            self.context_modeler.probability_codeblock_flag.estimate_bits(
                coded_block_flag
            )
        )
        if not coded_block_flag:
            return

        last_scan_index = np.max(np.nonzero(q_indexes))
        self.exp_golomb_prob_adapted(
            last_scan_index,
            self.context_modeler.probability_last_prefix,
            estimation=True,
        )

        self.estimate_q_index_bits(
            q_indexes[last_scan_index], last_scan_index, is_last=True
        )
        for index in range(last_scan_index - 1, -1, -1):
            self.estimate_q_index_bits(q_indexes[index], index)

    def estimate_q_index_bits(self, q_index, index, is_last=False):
        self.context_modeler.switch_context(index)

        if q_index == 0:
            self.estimated_bits += (
                self.context_modeler.probability_signal_flag.estimate_bits(0)
            )
            return
        elif abs(q_index) == 1:
            if not is_last:
                self.estimated_bits += (
                    self.context_modeler.probability_signal_flag.estimate_bits(1)
                )
            self.estimated_bits += (
                self.context_modeler.probability_gt1_flag.estimate_bits(0)
            )
            self.estimated_bits += 1
            return
        if not is_last:
            self.estimated_bits += (
                self.context_modeler.probability_signal_flag.estimate_bits(1)
            )

        self.estimated_bits += self.context_modeler.probability_gt1_flag.estimate_bits(
            1
        )
        self.exp_golomb_prob_adapted(
            abs(q_index) - 2,
            self.context_modeler.probability_level_prefix,
            estimation=True,
        )
        self.estimated_bits += 1

    def exp_golomb_prob_adapted(self, value: int, prob, estimation=False):
        assert value >= 0

        class_index = count_bits(value + 1) - 1  # class index

        if not estimation:
            self.arithmetic_encoder.encode_bits(1, class_index + 1, prob)
            self.arithmetic_encoder.encode_bits_bypass(value + 1, class_index)
        else:
            self.estimated_bits += class_index  # suffix part (bypass coded)
            while class_index > 0:
                class_index -= 1
                self.estimated_bits += prob.estimate_bits(0)
            self.estimated_bits += prob.estimate_bits(1)

    def terminate(self):
        self.arithmetic_encoder.terminate()
        return True
