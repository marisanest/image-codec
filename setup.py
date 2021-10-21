from setuptools import find_packages
from setuptools import setup

install_requires = [
    "numpy",
    "typing",
    "dataclasses",
    "scipy",
]

development_requires = ["black", "pytest"]

setup(
    name="image-codec",
    version="1.0",
    description="Tool to encode and decode images.",
    url="https://github.com/marisanest/image-codec",
    license="MIT",
    packages=find_packages(include=["image_codec*"]),
    install_requires=install_requires,
    extras_require={"development": development_requires},
    include_package_data=True,
)
