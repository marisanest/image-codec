# image-codec

[![Python 3.8](https://img.shields.io/badge/python-3.8-turquoise.svg)](https://www.python.org/downloads/release/python-380/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

The `image-codec` is a  simple CLI tool to encode and decode PGM images.

## Dependencies

- [Python 3.8](https://www.python.org/)

## Installation

### Production

To install the `image-codec` package for production purposes please, follow the subsequent instructions. All instructions also work for Python's and Anaconda's virtual environments.

If you want to use `git clone` together with `pip`, you can run:

```bash
git clone https://github.com/marisanest/image-codec.git
cd image-codec
```

Optionally, If you want to install a specific branch, please check out the wanted branch first:

```bash
git checkout <branch-name>
```

Then install the package:

```bash
pip install .
```

If you want to use `pip` only, you can run:

```bash
pip install git+https://github.com/marisanest/image-codec
```

Optionally, If you want to install a specific branch, please run the following command:

```bash
pip install git+https://github.com/marisanest/image-codec@<branch-name>
```

### Development

To install the `image-codec` package for development purposes please, follow the subsequent instructions.

If you want to use `git clone` together with `pip`, you can run:

```bash
git clone https://github.com/marisanest/image-codec.git
cd image-codec
```

Optionally, If you want to install a specific branch, please check out the wanted branch first:

```bash
git checkout <branch-name> 
```

Then install the package:

```bash
pip install -e .[development]
```

## Usage

For simple usage of the `image-codec` run for encoding:
```bash
image-codec encode <input-path> <output-path>
```
and for decoding: 
```bash
image-codec decode <input-path> <output-path>
```

For further details please run:

```bash
image-codec --help

Usage: image-codec [OPTIONS] COMMAND [ARGS]...

  A Image Codec CLI to en- and decode images.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  decode  Decode image.
  encode  Encode image.
```

## Results

Comparing a classical JPEG codec with this codec using a PSNR (Peak Signal-to-Noise Ratio) measurement, leads to the following quality improvements for an example image:

![](https://github.com/marisanest/image-codec/test/psnr_test_image.pdf)

## License
This library is available under the [MIT License](https://github.com/git/git-scm.com/blob/master/MIT-LICENSE.txt).
