# Installation

*datalab* is intended to be deployed on a persistent server accessible on the web that can act as a data management platform
for a group of researchers.

You may personally be looking for how to interact with an existing *datalab*
instance, in which case please check out the separate Python API package at
[datalab-org/datalab-api](https://github.com/datalab-org/datalab-python-api).

The instructions below outline how to make a development installation on your local machine.
We strongly recommend following the deployment instructions on [docs.datalab-org.io](https://docs.datalab-org.io/en/stable/deployment/) if you are deploying for use in production.

This repository consists of two components:

- a Flask-based Python web server (`pydatalab`) that communicates with the database backend
- a Vue.js web application for the user interface.

`pydatalab` can in principle be used without the web app frontend through its JSON API.

## Local (development) installation

To run *datalab*, you will need to install the environments for each component.

Firstly, from the desired folder, clone this repository from GitHub to your local machine with `git clone https://github.com/datalab-org/datalab`.
If you are not familiar with `git` or GitHub, you can do worse than reading through the [GitHub getting started documentation](https://docs.github.com/en/get-started/start-your-journey/about-github-and-git).

### `pydatalab` server installation

The instructions in this section will leave you with a running *datalab* server on your host machine, as implemented in the `pydatalab` Python package.

#### Database installation

*datalab* uses MongoDB as its database backend.
This requires a MongoDB server to be running on your desired host machine.

1. Install the free MongoDB community edition (see the full instructions for your OS on the [MongoDB website](https://docs.mongodb.com/manual/installation/)).
    * For MacOS users, MongoDB is available via [HomeBrew](https://github.com/mongodb/homebrew-brew).
    * You can alternatively run the MongoDB via Docker using the config in this package with `docker compose up database` (see [deployment instructions](deployment.md)).
    * If you wish to view the database directly, MongoDB has several GUIs, e.g. [MongoDB Compass](https://www.mongodb.com/products/compass) or [Studio 3T](https://robomongo.org/).
    * For persistence, you will need to set up MongoDB to run as a service on your computer (or run manually each time you run the `pydatalab` server).

#### Python setup

The next step is to set up a Python environment that contains all of the required dependencies with the correct versions.
You will need Python 3.10 or higher to run *datalab*; we recommend using a tool to manage Python versions on your machine, to avoid breakages based on your OS's Python versioning (e.g., [`pyenv`](https://github.com/pyenv/pyenv) or [`uv`](https://github.com/astral-sh/uv)).

##### Installation with `uv` or `venv`

We recommend using [`uv`](https://github.com/astral-sh/uv) (see the linked repository or https://docs.astral.sh/uv for installation instructions) for managing your *datalab* installation.

You could also use the standard library `venv` module, but this will not allow you to install pinned dependencies as easily, and is significantly slower than `uv`.

1. Create a virtual environment for *datalab*, ideally inside the `pydatalab` directory.
    - For `uv`, you can run `uv venv` (when installing using `uv sync`, this will be done automatically on installation).
    - For `venv`, this can be done with `python -m venv .venv`.
    - Either way, you will be left with a folder called `.venv` in your `pydatalab` directory that bundles an entire Python environment.
2. Activate the virtual environment (again, optional for `uv`) and install dependencies. One can either use the loosely pinned dependencies in `pyproject.toml`, or the locked versions in `uv.lock`.

=== "Installation with `uv`"

    ```shell
    # EITHER: Install all dependencies with locked versions (recommended)
    uv sync --all-extras --dev --locked
    # OR: Install all dependencies with loosely pinned versions
    uv pip install -e '.[all]'
    ```

=== "Installation with `venv`"

    ```shell
    source .venv/bin/activate
    # Install all dependencies with loosely pinned versions
    pip install -e '.[all]'
    ```

#### Running the development server

1. Run the server from the `pydatalab` folder with either:

=== "Launching with `uv`"

    ```shell
    cd pydatalab
    uv run flask --app 'pydatalab.main' run --reload --port 5001
    ```

=== "Launching with `venv`"

    ```shell
    cd pydatalab
    source .venv/bin/activate
    flask --app 'pydatalab.main' run --reload --port 5001
    ```

The server should now be accessible at [http://localhost:5001](http://localhost:5001).
If the server is running, navigating to this URL will display a simple dashboard.

Should you wish to contribute to/modify the Python code, you may wish to perform these extra steps:

1. From an activated virtual environment (or prepending `uv run`), run `pre-commit install` to begin using `pre-commit` to check all of your modifications when you run `git commit`.
    - The hooks that run on each commit can be found in the top-level `.pre-commit-config.yml` file.
1. From an activated virtual environment, the tests on the Python code can be run by executing `pytest` from the `pydatalab/` folder (or `uv run pytest`).

#### Additional notes

- If the Flask server is running when the source code is changed, it will generally hot-reload without needing to manually restart the server.
This can be controlled with the `--reload` flag to the `flask run` command.
- You may have to set `MONGO_URI` in your config file or environment variables (`PYDATALAB_MONGO_URI`) depending on your MongoDB setup, to e.g., `PYDATALAB_MONGO_URI=mongodb://localhost:27017/datalabvue`.

### Web app

1. If you do not already have it, install `node.js` v20 or above and the Node Package Manager (`npm`).
It is recommended not to install node using the official installer, since it is difficult to manage or uninstall, and permissions issues may arise.
Instead, it is recommended to install and manage versions using the [node version manager (nvm)](https://github.com/nvm-sh/nvm#installing-and-updating): `nvm install --lts`.
This will install the current recommended version of node and nvm.

2. Once installed, use it to install the `yarn` package manager: `npm install --global yarn`
From this point on, the `npm` command is not needed - all package and script management for the webapp is handled using `yarn`.
3. Navigate to the `webapp/` directory in your local copy of this repository and run `yarn install` (requires ~400 MB of disk space).
4. Run the webapp from a development server with `yarn serve`.

#### Additional notes

Similar to the Flask development server, these steps will provide a development environment that serves the web app at [http://localhost:8081](http://localhost:8081) (by default) and automatically reloads it as changes are made to the source code.

Various other development scripts are available through `yarn`:

- `yarn lint`: Lint the JavaScript code using `eslint`, identifying issues and automatically fixing many. This linting process also runs automatically every time the development server reloads.
- `yarn test:unit`: run the unit/component tests using `jest`. These test individual functions or components.
- `yarn test:e2e`: run end-to-end tests using `cypress`. This will build and serve the app, and launch an instance of Chrome where the tests can be interactively viewed. The tests can also be run without the GUI using ```yarn test:e2e --headless```. Note: currently, the tests make requests to the server running on `localhost:5001`.
- `yarn build`: Compile an optimised, minimised, version of the app for production.

## Development notes

### Adding new dependencies

Previously, *datalab* used `pipenv` for dependency management, which enforced a
strict lockfile of dependencies that effectively forced all dependencies to be updated when
adding a new one.
This is no longer the case, and the `pyproject.toml` file is now the canonical
source of dependencies, with `uv.lock` providing the strict locked versions for
testing.
Now, we use the `uv` functionality to create lock files
(and thus it is assumed that you installed the package in a `uv` virtual
environment, as described above).

To add a new dependency, add it to the `pyproject.toml` file in the
appropriate section (e.g., `[project.optional-dependencies.server]` for general dependencies, or `[project.optional-dependencies.apps]` for block-specific dependencies).
Ideally, this should be added with a "tilde" version specifier (`~=`) to ensure
that the dependency is updated to the latest compatible version when the
underlying project updates.

Finally, recreate the lock files with:

```shell
uv lock
```
### Test server authentication/authorisation

There are two approaches to authentication when developing *datalab* features locally.

1. Disable authentication entirely with the `PYDATALAB_TESTING=true` environment
   variable (or corresponding config file option `TESTING`). This will perform
   every API operation as if the user is authenticated, and will not require any
   further configuration.
   - This mode of development is fine for e.g., developing new blocks, but in
     cases where new API functionality is being added, it is recommended to set
     up authentication locally (see below).
1. Local OAuth setup. This requires registering an OAuth app with one of the
   implemented providers (e.g., GitHub, ORCID), configuring the credentials
   locally (see the [configuration documentation](https://docs.datalab-org.io/en/latest/config/) for more details) and then logging into *datalab* normally.
   - In this case, the user will also need to be activated when it is created.
     This can be done by manually editing the user in the database (setting
     `account_status` to `'active'`), or by running the `admin.activate-user`
     invoke task.
   - For testing admin functionality, the user can also be promoted with
     the `admin.change-user-role` invoke task.

Finally, all API tests can be run with variable authentication.
There are [pytest fixtures](https://docs.pytest.org/en/7.1.x/how-to/fixtures.html) that provide
test clients for unauthenticated, unauthorized, normal user and admin user
access.
As many authorisation cases should be tested as possible.
