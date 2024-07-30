#!/bin/sh
set -e

echo -e "\n-o- Setting commit user -o-"
git config --global user.email "${GIT_USER_EMAIL}"
git config --global user.name "${GIT_USER_NAME}"

echo "\n-o- Update version -o-"
cd pydatalab
pipenv run invoke dev.set-version -v ${GITHUB_REF#refs/tags/}

echo "\n-o- Commit updates - Changelog -o-"
git add pydatalab/__init__.py
git commit --allow-empty -m "Release ${GITHUB_REF#refs/tags/}"

echo -e "\n-o- Update version tag -o-"
git tag -f ${GITHUB_REF#refs/tags/}
