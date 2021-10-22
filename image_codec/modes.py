from enum import IntEnum


class PartitioningMode(IntEnum):
    NON_SUB_PARTITIONING: int = 0
    SUB_PARTITIONING: int = 1


class PredictionMode(IntEnum):
    DC_PREDICTION: int = 0
    VERTICAL_PREDICTION: int = 1
    HORIZONTAL_PREDICTION: int = 2
    PLANAR_PREDICTION: int = 3
