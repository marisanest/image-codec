from tqdm import tqdm

from ..bitstreams.output import OutputBitstream
from ..block import Block
from .entropy import EntropyEncoder
from ..frame import Frame
from ..modes import PartitioningMode, PredictionMode
from ..parameters import (
    PredictionModeParameters,
    PartitioningModeParameters,
    ParametersList,
    MetaParameters,
)
from ..predictor import Predictor
from ..transformer import Transformer


class Encoder:
    def __init__(
        self,
        input_path: str,
        output_path: str,
        block_size: int,
        quality_parameter: int,
        reconstruction_path: str = None,
    ):
        self.output_bitstream = OutputBitstream(output_path)
        self.frame = Frame.load(input_path, block_size)
        self.meta_parameters = MetaParameters(
            height=self.frame.height,
            width=self.frame.width,
            block_size=block_size,
            quality_parameter=quality_parameter,
        )
        self.reconstructed_frame = self.meta_parameters.build_frame()
        self.reconstruction_path = reconstruction_path
        self.transformer = Transformer(self.meta_parameters.block_size)
        self.predictor = Predictor(self.reconstructed_frame)
        self.entropy_encoder = EntropyEncoder(
            self.output_bitstream, self.meta_parameters.block_size
        )

    def encode(self):
        self.meta_parameters.encode(self.output_bitstream)

        for block in tqdm(self.frame.blocks()):
            self.entropy_encoder.encode_block(self.find_optimal_parameters(block))

        self.terminate()
        self.save()

    def terminate(self):
        self.entropy_encoder.terminate()
        self.output_bitstream.terminate()

    def save(self):
        if self.reconstruction_path:
            self.reconstructed_frame.save(self.reconstruction_path)

    def find_optimal_parameters(self, block: Block) -> PartitioningModeParameters:
        partitioning_modes_parameters = ParametersList()
        for partitioning_mode in PartitioningMode:
            partitioning_mode_parameters = PartitioningModeParameters(
                0, partitioning_mode
            )
            for index, partition in enumerate(block.partitions(partitioning_mode)):
                prediction_modes_parameters = ParametersList()
                for prediction_mode in PredictionMode:
                    partition.encode(
                        prediction_mode,
                        self.predictor,
                        self.meta_parameters.quantization_step_size,
                        self.transformer,
                    )
                    partition.estimate_bit_rate(
                        partitioning_mode,
                        prediction_mode,
                        self.entropy_encoder,
                        is_first_partition=index == 0,
                    )
                    cost = (
                        partition.distortion()
                        + self.meta_parameters.lagrange_multiplier
                        * partition.bit_rate_estimation
                    )

                    prediction_modes_parameters.append(
                        PredictionModeParameters(
                            cost,
                            prediction_mode,
                            partition.copy(),
                        )
                    )
                optimal_prediction_mode_parameters = (
                    prediction_modes_parameters.optimal()
                )
                partitioning_mode_parameters.merge(optimal_prediction_mode_parameters)
                self.reconstructed_frame.update(
                    optimal_prediction_mode_parameters.block, use_reconstruction=True
                )

            partitioning_modes_parameters.append(partitioning_mode_parameters)
            self.reconstructed_frame.reset(block)

        optimal_partitioning_modes_parameters = partitioning_modes_parameters.optimal()

        for (
            prediction_mode_parameters
        ) in optimal_partitioning_modes_parameters.prediction_mode_parameters_list:
            self.reconstructed_frame.update(
                prediction_mode_parameters.block, use_reconstruction=True
            )

        return optimal_partitioning_modes_parameters
