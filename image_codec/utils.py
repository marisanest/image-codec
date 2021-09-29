import numpy as np


def sort_diagonal(block: np.ndarray) -> np.ndarray:
    sorted_block = []
    rows, columns = block.shape

    for line in range(1, rows + columns):
        start_column = max(0, line - rows)
        count = min(line, (columns - start_column), rows)
        for j in range(0, count):
            sorted_block.append(block[min(rows, line) - j - 1][start_column + j])

    return np.array(sorted_block)


def invert_diagonal_sort(block: np.ndarray) -> np.ndarray:
    x = 0
    y = 0
    x_start = 0

    height = block.shape[0]
    sorted_block = np.zeros(block.shape, dtype=block.dtype)
    block = block.flatten()

    for index in range(block.size):
        sorted_block[y][x] = block[index]
        x += 1
        y -= 1
        if y < 0 or x >= height:
            y = min(x, height - 1)
            if x >= height:
                x_start += 1
            x = x_start

    return sorted_block


def count_bits(bit_pattern: int) -> int:
    counter = 0
    while bit_pattern != 0:
        bit_pattern = int(bit_pattern // 2)
        counter += 1
    return counter


def sign(bit: int):
    return 1 if bit else -1
