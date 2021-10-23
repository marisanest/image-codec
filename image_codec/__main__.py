import click
import time

from image_codec.encoders.encoder import Encoder
from image_codec.decoders.decoder import Decoder


@click.group()
@click.version_option("1.0.0")
def main():
    """A Image Codec CLI to en- and decode images."""
    pass


@main.command()
@click.argument('input-path', required=True, type=click.Path(exists=True))
@click.argument('output-path', required=True, type=click.Path())
@click.option("-bs", "--block-size", default=16, show_default=True, type=int, help="Block size of the encoder.")
@click.option(
    "-qp", "--quality-parameter", default=12, show_default=True, type=click.IntRange(0, 31),
    help="Quality parameter of the encoder (same as the quantization step size). [range: 0,31]",
)
@click.option(
    "-r", "--reconstruction-path", type=str,
    help="reconstruction path of the encoder (reconstructed image). If not given, no reconstruction will be saved.",
)
def encode(**kwargs):
    """Encode image."""
    print("Start encoding process...")
    start_time = time.process_time()

    print("Processing...")
    encoder = Encoder(
        kwargs.get("input_path"),
        kwargs.get("output_path"),
        kwargs.get("block_size"),
        kwargs.get("quality_parameter"),
        kwargs.get("reconstruction_path"),
    )
    encoder.encode()

    print(
        f"Finished encoding process in {(time.process_time() - start_time) * 1000} ms."
    )


@main.command()
@click.argument('input-path', required=True, type=click.Path(exists=True))
@click.argument('output-path', required=True, type=click.Path())
def decode(**kwargs):
    """Decode image."""
    print("Start decoding process...")
    start_time = time.process_time()

    print("Decoding...")
    decoder = Decoder(kwargs.get("input_path"), kwargs.get("output_path"))
    decoder.decode()

    print(
        f"Finished decoding process in {(time.process_time() - start_time) * 1000} ms."
    )


if __name__ == '__main__':
    main()
