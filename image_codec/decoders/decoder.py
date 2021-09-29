import numpy as np

from ..bitstreams.input import InputBitstream
from .entropy import EntropyDecoder
from ..frame import Frame
from ..parameters import MetaParameters
from ..predictor import Predictor
from ..transformer import Transformer


class Decoder:

    @classmethod
    def decode(cls, input_path: str, output_path: str):
        input_bitstream = InputBitstream(input_path)
        meta_parameters = MetaParameters.decode(input_bitstream)

        frame = Frame(
            np.zeros([meta_parameters.height, meta_parameters.width], dtype=np.uint8),
            meta_parameters.block_size
        )

        transformer = Transformer(meta_parameters.block_size)
        predictor = Predictor(frame)
        entropy_decoder = EntropyDecoder(input_bitstream, meta_parameters.block_size)

        for block in frame.blocks():
            for prediction_mode_parameters in entropy_decoder.decode_block(block).prediction_mode_parameters_list:
                prediction_mode_parameters.block.decode(
                    prediction_mode_parameters.prediction_mode,
                    predictor,
                    meta_parameters.quantization_step_size,
                    transformer
                )
                frame.update(prediction_mode_parameters.block, use_reconstruction=True)

        if not entropy_decoder.terminate():
            raise Exception('Arithmetic codeword not correctly terminated at end of frame')

        frame.save(output_path)

