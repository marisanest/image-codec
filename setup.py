import pathlib

from setuptools import find_packages, setup

install_requires = [
    "click",
    "numpy",
    "typing",
    "dataclasses",
    "scipy",
]

development_requires = ["black", "pytest"]

setup(
    name="image-codec",
    version="1.0.0",
    description="A simple CLI tool to encode and decode PGM images.",
    long_description=(pathlib.Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
    keyword="image codec pgm",
    license="MIT",
    url="https://github.com/marisanest/image-codec",
    packages=find_packages(include=["image_codec*"]),
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require={"development": development_requires},
    entry_points={
        "console_scripts": [
            "image-codec = image_codec.__main__:main",
        ],
    },
)
