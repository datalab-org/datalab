import re
from pathlib import Path
from typing import List, Union

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


def strip_reqs(fname: Union[str, Path]) -> List[str]:
    """Extract dependencies from a requirements.txt file that contains
    #-delimited comments and any pip-specific arguments.

    Parameters:
        fname: The filename to read.

    Returns:
        Each requirements line found in the file.

    """
    with open(fname, "r") as f:
        reqs = [
            line.strip()
            for line in f.readlines()
            if line.strip() and not line.strip()[0] in ("#", "-")
        ]
    return reqs


requirements = strip_reqs("./requirements.txt")
dev_requirements = strip_reqs("./requirements-dev.txt")

setup(
    name="pydatalab",
    version=VERSION,
    url="https://github.com/the-grey-group/datalabvue",
    include_package_data=True,
    packages=find_packages(),
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
    },
)
