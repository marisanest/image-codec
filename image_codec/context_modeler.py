import numpy as np

from typing import List

from .probability_model import ProbabilityModel


class ContextModeler:
    def __init__(self, block_size: int):
        self.probability_signal_flag = None
        self.probability_gt1_flag = None
        self.probability_level_prefix = None
        self.probability_coded_block_flag = ProbabilityModel()
        self.probability_last_prefix = ProbabilityModel()
        self.prediction_mode_bit1 = ProbabilityModel()
        self.prediction_mode_bit2 = ProbabilityModel()
        self.prediction_mode_bit3 = ProbabilityModel()
        self.partitioning_mode_bit = ProbabilityModel()
        self.probability_models_signal_flag = self.init_probability_models(3)
        self.probability_models_gt1_flag = self.init_probability_models(3)
        self.probability_models_level_prefix = self.init_probability_models(3)
        self.diagonal_map = self.generate_diagonal_map(block_size)

    def switch_context(self, index: int):
        if self.diagonal_map[index] < 4:
            probability_model_index = 0
        elif self.diagonal_map[index] < 7:
            probability_model_index = 1
        else:
            probability_model_index = 2

        self.probability_signal_flag = self.probability_models_signal_flag[
            probability_model_index
        ]
        self.probability_gt1_flag = self.probability_models_gt1_flag[
            probability_model_index
        ]
        self.probability_level_prefix = self.probability_models_level_prefix[
            probability_model_index
        ]

    @staticmethod
    def init_probability_models(n_probability_models: int) -> List[ProbabilityModel]:
        models = []
        for _ in range(n_probability_models):
            models.append(ProbabilityModel())
        return models

    @staticmethod
    def generate_diagonal_map(block_size: int) -> np.array:
        diagonal_map = []
        rows, columns = block_size, block_size

        for line in range(1, rows + columns):
            start_column = max(0, line - rows)
            count = min(line, (columns - start_column), rows)

            for j in range(0, count):
                l = min(rows, line) - j - 1
                r = start_column + j
                diagonal_map.append(l + r)

        return np.array(diagonal_map)
