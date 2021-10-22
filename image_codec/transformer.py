import math
import numpy as np
from scipy.fftpack import dct, idct

from .modes import PredictionMode


class Transformer:
    def __init__(self, block_size: int):
        self.dst_vii_matrices = {
            str(block_size): self.generate_dst_vii_matrix(block_size)
            for block_size in [block_size, int(block_size / 2)]
        }
        self.dst_vii_inverse_matrices = {
            str(block_size): self.dst_vii_matrices[str(block_size)].T
            for block_size in [block_size, int(block_size / 2)]
        }

    @staticmethod
    def generate_dst_vii_matrix(block_size):
        matrix = []
        beta = math.sqrt(4 / (2 * block_size + 1))
        for k in range(block_size):
            b_k = []
            for n in range(block_size):
                b_k.append(
                    beta
                    * math.sin(math.pi * ((2 * k + 1) / (2 * block_size + 1)) * (n + 1))
                )
            matrix.append(b_k)
        return np.asarray(matrix)

    def transform_forward(
        self, block: 'block.Block', prediction_mode: PredictionMode
    ) -> np.array:
        dst_vii_matrix_key = str(block.block_size)
        dst_vii_matrix = self.dst_vii_matrices[dst_vii_matrix_key]
        dst_vii_inverse_matrix = self.dst_vii_inverse_matrices[dst_vii_matrix_key]

        if prediction_mode == PredictionMode.PLANAR_PREDICTION:
            return np.matmul(
                np.matmul(dst_vii_matrix, block.prediction_error),
                dst_vii_inverse_matrix,
            )
        elif prediction_mode == PredictionMode.DC_PREDICTION:
            return dct(
                dct(block.prediction_error, axis=0, norm='ortho'), axis=1, norm='ortho'
            )
        elif prediction_mode == PredictionMode.HORIZONTAL_PREDICTION:
            return np.matmul(
                dct(block.prediction_error, axis=0, norm='ortho'),
                dst_vii_inverse_matrix,
            )
        else:
            return dct(
                np.matmul(dst_vii_matrix, block.prediction_error), axis=1, norm='ortho'
            )

    def transform_backward(
        self, block: 'block.Block', prediction_mode: PredictionMode
    ):
        dst_vii_matrix_key = str(block.block_size)
        dst_vii_matrix = self.dst_vii_matrices[dst_vii_matrix_key]
        dst_vii_inverse_matrix = self.dst_vii_inverse_matrices[dst_vii_matrix_key]

        if prediction_mode == PredictionMode.PLANAR_PREDICTION:
            rec_residual = np.matmul(
                np.matmul(dst_vii_inverse_matrix, block.reconstruction), dst_vii_matrix
            )
        elif prediction_mode == PredictionMode.DC_PREDICTION:
            rec_residual = idct(
                idct(block.reconstruction, axis=0, norm='ortho'), axis=1, norm='ortho'
            )
        elif prediction_mode == PredictionMode.HORIZONTAL_PREDICTION:
            rec_residual = np.matmul(
                idct(block.reconstruction, axis=0, norm='ortho'), dst_vii_matrix
            )
        else:
            rec_residual = idct(
                np.matmul(dst_vii_inverse_matrix, block.reconstruction),
                axis=1,
                norm='ortho',
            )

        return np.rint(rec_residual).astype(int)
