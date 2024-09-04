#!/bin/bash

# This script is a hack to keep a pipenv lock synced with our pip-compile files
# It injects dynamic optional dependencies into our pyproject.toml (currently incompatible
# with any non-dynamic dependencies in setuptools 74) and generates the lock file
#

TOP_DIR=$(git rev-parse --show-toplevel)
# Strip comments
sed -i '/^\s&*#/d' $TOP_DIR/pydatalab/requirements/*.txt
cd $TOP_DIR/pydatalab && pipenv install -r requirements/requirements-all.txt && pipenv install -r requirements/requirements-all-dev.txt --dev
# Reset Pipfile, which will now have all deps inlined
 cd $TOP_DIR/pydatalab && git checkout requirements
