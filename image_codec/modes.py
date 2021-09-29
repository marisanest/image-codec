from enum import IntEnum


class PartitioningMode(IntEnum):
    NON_SUB_PARTITIONING = 0
    SUB_PARTITIONING = 1


class PredictionMode(IntEnum):
    DC_PREDICTION = 0
    VERTICAL_PREDICTION = 1
    HORIZONTAL_PREDICTION = 2
    PLANAR_PREDICTION = 3
