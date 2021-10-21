import argparse
import time

from image_codec.Decoder import Decoder


def main():
    parser = argparse.ArgumentParser(description="image decoder")

    parser.add_argument(
        "-i",
        "--input-path",
        help="input path for the decoder (encoded image).",
        required=True,
        dest="input_path",
    )

    parser.add_argument(
        "-o",
        "--output-path",
        help="output path for the decoder (decoded image).",
        required=True,
        dest="output_path",
    )

    args = parser.parse_args()

    print("Start decoding process...")
    start_time = time.process_time()

    print("Decoding...")
    Decoder(args.input_path, args.output_path).decode()

    print(
        f"Finished decoding process in {(time.process_time() - start_time) * 1000} ms."
    )


if __name__ == "__main__":
    main()
