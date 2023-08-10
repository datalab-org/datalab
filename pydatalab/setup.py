import re
from pathlib import Path

from setuptools import find_packages, setup

module_dir = Path(__file__).resolve().parent

with open(module_dir.joinpath("pydatalab/__init__.py")) as version_file:
    for line in version_file:
        match = re.match(r'__version__ = "(.*)"', line)
        if match is not None:
            VERSION = match.group(1)
            break
    else:
        raise RuntimeError(f"Could not determine package version from {version_file.name} !")


setup(
    name="pydatalab",
    version=VERSION,
    url="https://github.com/the-grey-group/datalab",
    include_package_data=True,
    packages=find_packages(),
    python_requires=">=3.9",
)
