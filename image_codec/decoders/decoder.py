from ..bitstreams.input import InputBitstream
from .entropy import EntropyDecoder
from ..parameters import MetaParameters
from ..predictor import Predictor
from ..transformer import Transformer


class Decoder:
    def __init__(self, input_path: str, output_path: str):
        self.input_bitstream = InputBitstream(input_path)
        self.output_path = output_path
        self.meta_parameters = MetaParameters.decode(self.input_bitstream)
        self.decoded_frame = self.meta_parameters.build_frame()
        self.transformer = Transformer(self.meta_parameters.block_size)
        self.predictor = Predictor(self.decoded_frame)
        self.entropy_decoder = EntropyDecoder(
            self.input_bitstream, self.meta_parameters.block_size
        )

    def decode(self):
        for block in self.decoded_frame.blocks():
            for parameters in self.entropy_decoder.decode_block(
                block
            ).prediction_mode_parameters_list:
                parameters.block.decode(
                    parameters.prediction_mode,
                    self.predictor,
                    self.meta_parameters.quality_parameter,
                    self.transformer,
                )
                self.decoded_frame.update(parameters.block, use_reconstruction=True)

        self.terminate()
        self.save()

    def terminate(self):
        self.entropy_decoder.terminate()
        self.input_bitstream.terminate()

    def save(self):
        self.decoded_frame.save(self.output_path)
