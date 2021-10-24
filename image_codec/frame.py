import numpy as np

from typing import List

from .block import Block


class Frame:
    def __init__(self, data: np.array, block_size: int):
        self.data = data
        self.height, self.width = data.shape
        self.block_size = block_size
        self.padding_height = (
            self.block_size - self.height % self.block_size
            if self.height % self.block_size != 0
            else 0
        )
        self.padding_width = (
            self.block_size - self.width % self.block_size
            if self.width % self.block_size != 0
            else 0
        )
        self.data = np.pad(
            self.data, ((0, self.padding_height), (0, self.padding_width)), "edge"
        )

    def blocks(self) -> List[Block]:
        for y in range(0, self.height + self.padding_height, self.block_size):
            for x in range(0, self.width + self.padding_width, self.block_size):
                yield Block(
                    x,
                    y,
                    self.block_size,
                    self[y : y + self.block_size, x : x + self.block_size],
                )

    def update(self, block: Block, use_reconstruction: bool = False):
        self[
            block.y : block.y + block.block_size, block.x : block.x + block.block_size
        ] = (block.reconstruction if use_reconstruction else block.data)

    def reset(self, block: Block):
        self[
            block.y : block.y + block.block_size, block.x : block.x + block.block_size
        ] = 0

    def __setitem__(self, index: int, data: np.array):
        self.data[index] = data

    def __getitem__(self, index: int) -> int:
        return self.data[index]

    @staticmethod
    def load(input_path: str, block_size: int) -> "frame.Frame":
        with open(input_path, "rb") as file:
            header = file.readline()

            if header != b"P5\n":
                raise Exception("Frame: Not an PGM image.")

            size = file.readline()
            max_value = file.readline()

            if max_value != b"255\n":
                raise Exception("Frame: PGM image has unexpected bit depth.")

            width, height = str(size).split(" ")
            width = int(width[2:])
            height = int(height[: len(height) - 3])
            data = np.zeros([height, width], dtype=np.uint8)

            for yi in range(0, height):
                for xi in range(0, width):
                    byte = file.read(1)
                    if not byte:
                        raise Exception("Frame: PGM image is corrupted.")
                    data[yi, xi] = byte[0]

            return Frame(data, block_size)

    def save(self, output_path: str):
        with open(output_path, "wb") as file:
            file.write(f"P5\n{self.width} {self.height}\n255\n".encode())
            file.write(self.data[:self.height, :self.width].ravel().tobytes())
