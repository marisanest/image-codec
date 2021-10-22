import numpy as np

from .block import Block
from .frame import Frame
from .modes import PredictionMode


class Predictor:
    def __init__(self, frame: Frame):
        self.frame = frame

    def left_border(self, block: Block) -> np.array:
        return (
            self.frame[
                block.y : block.y + block.block_size, block.x - 1 : block.x
            ].ravel()
            if block.x > 0
            else np.full([block.block_size], 128)
        )

    def top_border(self, block: Block) -> np.array:
        return (
            self.frame[
                block.y - 1 : block.y, block.x : block.x + block.block_size
            ].ravel()
            if block.y > 0
            else np.full([block.block_size], 128)
        )

    def get_prediction(
        self, block: Block, prediction_mode: PredictionMode
    ) -> np.ndarray:
        if prediction_mode == PredictionMode.DC_PREDICTION:
            return self.get_dc_prediction(block)
        elif prediction_mode == PredictionMode.VERTICAL_PREDICTION:
            return self.get_vertical_prediction(block)
        elif prediction_mode == PredictionMode.HORIZONTAL_PREDICTION:
            return self.get_horizontal_prediction(block)
        else:
            return self.get_planar_prediction(block)

    def get_dc_prediction(self, block: Block) -> np.ndarray:
        dc = 128
        if block.x > 0 and block.y > 0:
            dc = round(
                0.5 * (self.left_border(block).mean() + self.top_border(block).mean())
            )
        elif block.x > 0:
            dc = round(self.left_border(block).mean())
        elif block.y > 0:
            dc = round(self.top_border(block).mean())
        return np.full([block.block_size, block.block_size], dc)

    def get_vertical_prediction(self, block: Block) -> np.ndarray:
        return np.full([block.block_size, block.block_size], self.top_border(block))

    def get_horizontal_prediction(self, block: Block) -> np.ndarray:
        return np.full([block.block_size, block.block_size], self.left_border(block)).T

    def get_planar_prediction(self, block: Block) -> np.ndarray:
        top_samples = self.top_border(block).astype("int")
        left_samples = self.left_border(block).astype("int")

        virtual_bottom_samples = np.full(
            [block.block_size], left_samples[block.block_size - 1]
        )
        virtual_right_samples = np.full(
            [block.block_size], top_samples[block.block_size - 1]
        )

        prediction = np.full(
            [block.block_size, block.block_size], block.block_size, dtype="int32"
        )

        for local_x in range(0, block.block_size):
            prediction[:, local_x] += (
                block.block_size - 1 - local_x
            ) * left_samples + (1 + local_x) * virtual_right_samples

        for local_y in range(0, block.block_size):
            prediction[local_y, :] += (block.block_size - 1 - local_y) * top_samples + (
                1 + local_y
            ) * virtual_bottom_samples

        prediction //= 2 * block.block_size

        return prediction
