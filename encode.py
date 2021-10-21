import argparse
import time

from image_codec.Encoder import Encoder


def main():
    parser = argparse.ArgumentParser(description="Image Encoder")

    parser.add_argument(
        "-i",
        "--input-path",
        help="input path of the encoder (original image).",
        required=True,
        dest="input_path",
    )

    parser.add_argument(
        "-o",
        "--output-path",
        help="output path of the encoder (encoded image).",
        required=True,
        dest="output_path",
    )

    parser.add_argument(
        "-bs",
        "--block-size",
        help="block size of the encoder (default: 16).",
        default=16,
        dest="block_size",
        type=int,
    )

    parser.add_argument(
        "-qp",
        "--quality-parameter",
        help="quality parameter of the encoder (effects to the quantization step size). range [0;31] (default: 12).",
        default=12,
        choices=(range(0, 32)),
        dest="quality_parameter",
        type=int,
    )

    parser.add_argument(
        "-r",
        "--reconstruction-path",
        help="reconstruction path of the encoder (reconstructed image). If not given, no reconstruction will be saved.",
        dest="reconstruction_path",
    )

    args = parser.parse_args()

    print("Start encoding process...")
    start_time = time.process_time()

    print("Encoding...")
    Encoder(
        args.input_path,
        args.output_path,
        args.block_size,
        args.quality_parameter,
        args.reconstruction_path,
    ).encode()

    print(
        f"Finished encoding process in {(time.process_time() - start_time) * 1000} ms."
    )


if __name__ == "__main__":
    main()
