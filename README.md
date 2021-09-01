# datalabvue

## Installation

This repository consists of two components:
- a Flask-based Python web server (`pydatalab`) that communicates with the database backend,
- a JavaScript+Vue web application for the user interface.

To run an instance, you will need to install the environments for each component.

Firstly, from the desired folder, clone this repository from GitHub to your local machine with `git clone https://github.com/the-grey-group/datalabvue`.

Alternatively, if you do not wish to contribute to the code, you can simply download the current state as a .zip file from [GitHub](https://github.com/the-grey-group/datalabvue/archive/refs/heads/main.zip).
Should you wish to just run the apps themselves, the easiest method is to use Docker ([instructions below](#deployment-with-docker).

### `pydatalab` server installation

1. Install `pipenv` on your machine.
    - Detailed instructions for installing `pipenv`, `pip` and Python itself can be found on the [`pipenv` website](https://pipenv.pypa.io/en/latest/install/#installing-pipenv).
    - We recommend you install `pipenv` from PyPI (with `pip install pipenv` or `pip install --user pipenv`) for the Python distribution of your choice (in a virtual environment or otherwise). This is distinct from the virtual environment that `pipenv` itself will create for the `pydatalab` package.

1. Set up MongoDB.
    1. Install the free MongoDB community edition (full instructions on the [MongoDB website](https://docs.mongodb.com/manual/installation/)).
        * For Mac users, MongoDB is available via [HomeBrew](https://github.com/mongodb/homebrew-brew).
        - You can alternatively run the MongoDB via Docker using the config in this package with `docker-compose up mongo` (see further instructions [below](#deployment-with-docker).
        * If you wish to view the database directly, MongoDB has several GUIs, e.g. [MongoDB Compass](https://www.mongodb.com/products/compass) or [RoboMongo](https://robomongo.org/).
        - For persistence, you will need to set up MongoDB to run as a service on your computer (or run manually each time you use the site).
    1. In MongoDB, create a database called "datalabvue" ([further instructions on the MongoDB website](https://www.mongodb.com/basics/create-database)).
        - You can do this with the `mongo` shell (`echo "use datalabvue" | mongo`) or with Compass.
1. Install the `pydatalab` package.
    1. Navigate to the `pydatalab` folder and run `pipenv install`.
        - This will create a `pipenv` environment for `pydatalab` and all of its dependencies that is registered within *this folder* only.
1. Run the server from the `pydatalab` folder with `pipenv run pydatalab/main.py`.

The server should now be accessible at http://localhost:5001. If the server is running, navigating to this URL will display "Hello, This is a server".

Should you wish to contribute to/modify the Python code, you may wish to perform these extra steps:

1. From within the `pydatalab` folder, run `pipenv install --dev` to pull the development dependencies (e.g., `pre-commit`, `pytest`).
1. Run `pre-commit install` to begin using `pre-commit` to check all of your modifications when you run `git commit`.
    - The hooks that run on each commit can be found in the top-level `.pre-commit-config.yml` file.
1. The tests on the Python code can be run by executing `py.test` from the `pydatalab/` folder.

Additional notes:

- If the Flask server is running when the source code is changed, it will generally hot-reload without needing to manually restart the server.
- You may have to configure the `MONGO_URI` config in `main.py` depending on your MongoDB setup. In the future, this will be accessible via a config file.

### Web app

1. If you do not already have it, install the Node Package Manager (`npm`) either from [their website](https://www.npmjs.com/get-npm) or your OS package manager, then use it to install the `yarn` package manager:

     ```npm install --global yarn```

    From this point on, the `npm` command is not needed - all package and script management for the webapp is handled using `yarn`.
1. Navigate to the `webapp/` directory in your local copy of this repository and run `yarn install` (requires ~300 MB of disk space).
1. Run the webapp from a development server with `yarn serve`. 

Similar to the Flask development server, these steps will provide a development environment that serves the web app at `localhost:8080` (by default) and automatically reloads it as changes are made to the source code.
Various other development scripts are available through `yarn` (see also the [webapp README](./webapp/README.md)):
    - `yarn lint`: Lint the javascript code using `eslint`, identifying issues and automatically fixing many. This linting process also runs automatically every time the development server reloads.
    - `yarn test:unit`: run the unit/componenet tests using `jest`. These test individual functions or components.
    - `yarn test:e2e`: run end-to-end tests using `cypress`. This will build and serve the app, and launch an instance of Chrome where the tests can be interactively viewed. The tests can also be run without the gui using ```yarn test:e2e --headless```. Note: currently, the tests make requests to the server running on `localhost:5001`.
    - `yarn build`: Compile an optimized, minimized, version of the app for production.


## Deployment with Docker

These instructions assume that both Docker and docker-compose are installed (and that the Docker daemon is running). See the [Docker website](https://docs.docker.com/compose/install/) for instructions.

Dockerfiles for the web app, server and database can be found in the `.docker` directory.
- `docker-compose build` will pull each of the base Docker images (`mongo`, `node` and `python`) and build the corresponding apps on top of them.
- `docker-compose up` will launch a container for each component, such that the web app can be accessed at `localhost:8080`, the server at `localhost:5001` and the database at `localhost:27017`. The source files for the server and the web app are copied at the build stage, so no hot-reloading will occur by default (so `docker-compose build` will need to be called again).
- `docker-compose stop` will stop all running containers.

## Note on remote filesystems

In order to use remote filesystems, you will have to (connect to the ChemNet VPN and) mount the Grey Group backup servers on your local machine.
Then, go into `resources.py` and change the paths to the folders you are interested in.
Remote access is currently very slow, so it is recommended that you restrict the folders to the smallest subset possible, i.e., just your personal folder on each given server.
