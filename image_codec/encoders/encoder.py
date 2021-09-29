import numpy as np
from tqdm import tqdm

from ..bitstreams.output import OutputBitstream
from ..block import Block
from .entropy import EntropyEncoder
from ..frame import Frame
from ..modes import PartitioningMode, PredictionMode
from ..parameters import PredictionModeParameters, PartitioningModeParameters, ParametersList, MetaParameters
from ..predictor import Predictor
from ..transformer import Transformer


class Encoder:

    @classmethod
    def encode(cls, input_path: str, output_path: str, block_size: int, quality_parameter: int,
               reconstruction_path: str = None):
        output_bitstream = OutputBitstream(output_path)
        frame = Frame.load(input_path, block_size)

        meta_parameters = MetaParameters(
            height=frame.height,
            width=frame.width,
            block_size=block_size,
            quality_parameter=quality_parameter,
        )

        meta_parameters.encode()

        transformer = Transformer(meta_parameters.block_size)

        reconstructed_frame = Frame(
            np.zeros((frame.height, frame.width), dtype=np.uint8),
            block_size
        )

        predictor = Predictor(reconstructed_frame)
        entropy_encoder = EntropyEncoder(output_bitstream, block_size)

        for block in tqdm(frame.blocks()):
            entropy_encoder.encode_block(
                cls.optimal_parameters(
                    block,
                    meta_parameters,
                    transformer,
                    reconstructed_frame,
                    predictor,
                    entropy_encoder
                )
            )

        entropy_encoder.terminate()
        output_bitstream.terminate()

        if reconstruction_path:
            frame.save(reconstruction_path)

    @staticmethod
    def optimal_parameters(block: Block, meta_parameters: MetaParameters, transformer: Transformer,
                           reconstructed_frame: Frame, predictor: Predictor, entropy_encoder: EntropyEncoder):
        partitioning_modes_parameters = ParametersList()
        for partitioning_mode in PartitioningMode:
            partitioning_mode_parameters = PartitioningModeParameters(0, partitioning_mode)
            for index, partition in enumerate(block.partitions(partitioning_mode)):
                prediction_modes_parameters = ParametersList()
                for prediction_mode in PredictionMode:
                    partition.encode(prediction_mode, predictor, meta_parameters.quantization_step_size, transformer)
                    partition.estimate_bit_rate(
                        partitioning_mode, prediction_mode, entropy_encoder, is_first_partition=index == 0
                    )
                    cost = partition.distortion() + meta_parameters.lagrange_multiplier * partition.bit_rate_estimation

                    prediction_modes_parameters.append(
                        PredictionModeParameters(
                            cost,
                            prediction_mode,
                            partition.copy(),
                        )
                    )
                optimal_prediction_mode_parameters = prediction_modes_parameters.optimal()
                partitioning_mode_parameters.merge(optimal_prediction_mode_parameters)
                reconstructed_frame.update(optimal_prediction_mode_parameters.block, use_reconstruction=True)

            partitioning_modes_parameters.append(partitioning_mode_parameters)
            reconstructed_frame.reset(block)

        optimal_partitioning_modes_parameters = partitioning_modes_parameters.optimal()

        for prediction_mode_parameters in optimal_partitioning_modes_parameters.prediction_mode_parameters_list:
            reconstructed_frame.update(prediction_mode_parameters.block, use_reconstruction=True)

        return optimal_partitioning_modes_parameters
