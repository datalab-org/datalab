# Installation

*datalab* is intended to be deployed on a persistent server accessible on the web that can act as a data management platform
for a group of researchers.
The instructions below outline how to make a development installation on your local machine.
We strongly recommend following the [deployment instructions](deployment.md) (or [here](https://the-datalab.readthedocs.io/en/latest/deployment) if you are reading this directly on GitHub) if you are deploying for use in production; these instructions may also be useful for developers who want to use Docker to create a reproducible development environment.

This repository consists of two components:

- a Flask-based Python web server (`pydatalab`) that communicates with the database backend
- a JavaScript+Vue web application for the user interface.

`pydatalab` can in principle be used without the web app frontend through its JSON API.

## Local (development) installation

To run *datalab*, you will need to install the environments for each component.

Firstly, from the desired folder, clone this repository from GitHub to your local machine with `git clone https://github.com/datalab-org/datalab`.

### `pydatalab` server installation

The instructions in this section will leave you with a running JSON API on your host machine.
This can hypothetically be used entirely independently from the web front-end through the JSON API.

1. Install `pipenv` on your machine.
    - Detailed instructions for installing `pipenv`, `pip` and Python itself can be found on the [`pipenv` website](https://pipenv.pypa.io/en/latest/install/#installing-pipenv). You will need Python 3.10 or higher to run pydatalab.
    - We recommend you install `pipenv` from PyPI (with `pip install pipenv` or `pip install --user pipenv`) for the Python distribution of your choice (in a virtual environment or otherwise). `pipenv` will be used to create its own virtual environment for installation of the `pydatalab` package.
1. Set up MongoDB.
    1. Install the free MongoDB community edition (full instructions on the [MongoDB website](https://docs.mongodb.com/manual/installation/)).
        * For Mac users, MongoDB is available via [HomeBrew](https://github.com/mongodb/homebrew-brew).
        - You can alternatively run the MongoDB via Docker using the config in this package with `docker-compose up mongo` (see further instructions [below](#deployment-with-docker).
        * If you wish to view the database directly, MongoDB has several GUIs, e.g. [MongoDB Compass](https://www.mongodb.com/products/compass) or [Studio 3T](https://robomongo.org/).
        - For persistence, you will need to set up MongoDB to run as a service on your computer (or run manually each time you run the `pydatalab` server).
    1. In MongoDB, create a database called "datalabvue" ([further instructions on the MongoDB website](https://www.mongodb.com/basics/create-database)).
        - You can do this with the `mongo` shell (`echo "use datalabvue" | mongo`) or with Compass.
1. Install the `pydatalab` dependencies.
    1. Navigate to the `datalab/pydatalab` folder and run `pipenv install`.
        - This will create a `pipenv` environment for `pydatalab` and all of its dependencies that is registered within *this folder* only.
1. Run the server from the `pydatalab` folder with `pipenv run python pydatalab/main.py`.
    1.  If you get an error `No module named pydatalab`, run `pipenv run pip install -e .` from the `datalab/pydatalab` folder and then try again.

The server should now be accessible at [http://localhost:5001](http://localhost:5001). If the server is running, navigating to this URL will display a simple dashboard with a textual list of available endpoints.

Should you wish to contribute to/modify the Python code, you may wish to perform these extra steps:

1. From within the `pydatalab` folder, run `pipenv install --dev` to pull the development dependencies (e.g., `pre-commit`, `pytest`).
1. Run `pre-commit install` to begin using `pre-commit` to check all of your modifications when you run `git commit`.
    - The hooks that run on each commit can be found in the top-level `.pre-commit-config.yml` file.
1. The tests on the Python code can be run by executing `py.test` from the `pydatalab/` folder.

#### Additional notes

- If the Flask server is running when the source code is changed, it will generally hot-reload without needing to manually restart the server.
- You may have to set `MONGO_URI` in your config file or environment variables (`PYDATALAB_MONGO_URI`) depending on your MongoDB setup.

### Web app

1. If you do not already have it, install `node.js` v20 or above and the Node Package Manager (`npm`).
It is recommended not to install node using the official installer, since it is difficult to manage or uninstall, and permissions issues may arise.
Intead, it is recommended to install and manage versions using the [node version manager (nvm)](https://github.com/nvm-sh/nvm#installing-and-updating): `nvm install --lts`.
This will install the current recommended version of node and nvm.

2. Once installed, use it to install the `yarn` package manager: `npm install --global yarn`
From this point on, the `npm` command is not needed - all package and script management for the webapp is handled using `yarn`.
3. Navigate to the `webapp/` directory in your local copy of this repository and run `yarn install` (requires ~400 MB of disk space).
4. Run the webapp from a development server with `yarn serve`.

#### Additional notes

Similar to the Flask development server, these steps will provide a development environment that serves the web app at [http://localhost:8081](http://localhost:8081) (by default) and automatically reloads it as changes are made to the source code.

Various other development scripts are available through `yarn`:

- `yarn lint`: Lint the javascript code using `eslint`, identifying issues and automatically fixing many. This linting process also runs automatically every time the development server reloads.
- `yarn test:unit`: run the unit/component tests using `jest`. These test individual functions or components.
- `yarn test:e2e`: run end-to-end tests using `cypress`. This will build and serve the app, and launch an instance of Chrome where the tests can be interactively viewed. The tests can also be run without the gui using ```yarn test:e2e --headless```. Note: currently, the tests make requests to the server running on `localhost:5001`.
- `yarn build`: Compile an optimized, minimized, version of the app for production.
