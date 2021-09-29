import numpy as np

from .modes import PartitioningMode, PredictionMode
from .transformer import Transformer
from .utils import sort_diagonal, invert_diagonal_sort


class Block:
    def __init__(self, x: int, y: int, block_size: int, data: np.array, prediction: np.array = None,
                 prediction_error: np.array = None, q_indexes: np.array = None, reconstruction: np.array = None,
                 bit_rate_estimation: int = None):
        self.x = x
        self.y = y
        self.block_size = block_size
        self.data = data
        self.prediction = prediction
        self.prediction_error = prediction_error
        self.q_indexes = q_indexes
        self.reconstruction = reconstruction
        self.bit_rate_estimation = bit_rate_estimation

    def partitions(self, partitioning_mode: PartitioningMode) -> list:
        partition_block_size = self.block_size if partitioning_mode == PartitioningMode.NON_SUB_PARTITIONING else int(self.block_size / 2)
        for partition_y in range(0, self.block_size, partition_block_size):
            for partition_x in range(0, self.block_size, partition_block_size):
                yield Block(
                    self.x + partition_x,
                    self.y + partition_y,
                    partition_block_size,
                    self.data[
                        partition_y:partition_y + partition_block_size,
                        partition_x:partition_x + partition_block_size
                    ]
                )

    def encode(self, prediction_mode: PredictionMode,
               prediction_calculator: 'PredictionCalculator.PredictionCalculator', qs: float,
               transformer: Transformer, inter: bool = False, mx: int = None, my: int = None):
        self.predict(prediction_mode, prediction_calculator, inter, mx, my)
        self.prediction_error = self.data.astype('int') - self.prediction
        transform_coefficients = transformer.transform_forward(self, prediction_mode)
        self.q_indexes = (
                    np.sign(transform_coefficients) * np.floor((np.abs(transform_coefficients) / qs) + 0.4)).astype(
            'int')
        self.reconstruct(prediction_mode, qs, transformer)
        self.sort_q_indexes(prediction_mode)

    def decode(self, prediction_mode: PredictionMode,
               prediction_calculator: 'PredictionCalculator.PredictionCalculator', qs: float,
               transformer: Transformer, inter: bool = False, mx: int = None, my: int = None):
        self.predict(prediction_mode, prediction_calculator, inter, mx, my)
        self.sort_q_indexes(prediction_mode, decode=True)
        self.reconstruct(prediction_mode, qs, transformer)

    def predict(self, prediction_mode: PredictionMode,
                prediction_calculator: 'PredictionCalculator.PredictionCalculator', inter: bool = False,
                mx: int = None, my: int = None):
        self.prediction = prediction_calculator.get_inter_prediction(self, mx, my) if inter else prediction_calculator.get_prediction(self, prediction_mode)

    def reconstruct(self, prediction_mode: PredictionMode, qs: float, transformer: Transformer):
        self.reconstruction = self.q_indexes * qs
        self.reconstruction = transformer.transform_backward(self, prediction_mode)
        self.reconstruction += self.prediction
        self.reconstruction = np.clip(self.reconstruction, 0, 255).astype('uint8')

    def sort_q_indexes(self, prediction_mode: PredictionMode, decode=False):
        if prediction_mode == PredictionMode.DC_PREDICTION or prediction_mode == PredictionMode.PLANAR_PREDICTION:
            self.q_indexes = invert_diagonal_sort(self.q_indexes) if decode else sort_diagonal(self.q_indexes)
        elif prediction_mode == PredictionMode.HORIZONTAL_PREDICTION:
            self.q_indexes = self.q_indexes.T

    def distortion(self):
        return np.sum(np.square(np.subtract(self.data, self.reconstruction, dtype='int')))

    def estimate_bit_rate(self, partitioning_mode: PartitioningMode, prediction_mode: PredictionMode,
                          entropy_encoder: 'EntropyEncoder.EntropyEncoder', is_first_partition: bool = True):
        self.bit_rate_estimation = entropy_encoder.estimate_block_bits(
            self, partitioning_mode, prediction_mode, is_first_partition=is_first_partition)

    def shape(self):
        return self.data.shape

    def copy(self):
        return Block(
            self.x,
            self.y,
            self.block_size,
            self.data.copy(),
            self.prediction.copy(),
            self.prediction_error.copy(),
            self.q_indexes.copy(),
            self.reconstruction.copy(),
            self.bit_rate_estimation,
        )
