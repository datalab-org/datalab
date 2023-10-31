# Installation

*datalab* is intended to be deployed on a persistent server accessible on the web that can act as a data management platform
for a given collection of researchers.
The instructions below outline how to make primarily a development installation on your local machine.
We strongly recommend using the [Docker setup instructions](#deployment-with-docker) if you are deploying to a server.

This repository consists of two components:

- a Flask-based Python web server (`pydatalab`) that communicates with the database backend,
- a JavaScript+Vue web application for the user interface.


## Local (development) installation

To run *datalab*, you will need to install the environments for each component.

Firstly, from the desired folder, clone this repository from GitHub to your local machine with `git clone https://github.com/the-grey-group/datalab`.

### `pydatalab` server installation

The instructions in this section will leave you with a running JSON API on your host machine.
This can hypothetically be used entirely independently (and hopefully increasingly ergonomically) from the web front-end.

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
1. Run the server from the `pydatalab` folder with `pipenv run python pydatalab/main.py`.

The server should now be accessible at [http://localhost:5001](http://localhost:5001). If the server is running, navigating to this URL will display a simple dashboard with a textual list of available endpoints.

Should you wish to contribute to/modify the Python code, you may wish to perform these extra steps:

1. From within the `pydatalab` folder, run `pipenv install --dev` to pull the development dependencies (e.g., `pre-commit`, `pytest`).
1. Run `pre-commit install` to begin using `pre-commit` to check all of your modifications when you run `git commit`.
    - The hooks that run on each commit can be found in the top-level `.pre-commit-config.yml` file.
1. The tests on the Python code can be run by executing `py.test` from the `pydatalab/` folder.

#### Additional notes

- If the Flask server is running when the source code is changed, it will generally hot-reload without needing to manually restart the server.
- You may have to set `MONGO_URI` in your config file or environment variables (`PYDATALAB_MONGO_URI`) depending on your MongoDB setup, further details can be found in the [Server Configuration](config.md) instructions.

### Web app

1. If you do not already have it, install node.js and the Node Package Manager (`npm`).
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
- `yarn test:unit`: run the unit/componenet tests using `jest`. These test individual functions or components.
- `yarn test:e2e`: run end-to-end tests using `cypress`. This will build and serve the app, and launch an instance of Chrome where the tests can be interactively viewed. The tests can also be run without the gui using ```yarn test:e2e --headless```. Note: currently, the tests make requests to the server running on `localhost:5001`.
- `yarn build`: Compile an optimized, minimized, version of the app for production.

## Deployment with Docker

[Docker](https://docs.docker.com/) uses virtualization to allow you to build "images" of your software that are transferrable and deployable as "containers" across multiple systems.
These instructions assume that Docker is installed (a recent version that includes Compose V2 and BuildKit) and that the Docker daemon is running locally.
See the [Docker website](https://docs.docker.com/compose/install/) for instructions for your system.
Note that pulling and building the images can require significant disk space (~5 GB for a full setup), especially when multiple versions of images have been built (you can use `docker system df` to see how much spaace is being used).

Dockerfiles for the web app, server and database can be found in the `.docker` directory.
There are separate build targets for `production` and `development` (and corresponding docker-compose profiles `prod` and `dev`).
The production target will copy the state of the repository on build and use `gunicorn` and `serve` to serve the server and app respectively.
The development target mounts the repository in the running container and provides hot-reloading servers for both the backend and frontend.
- `docker compose --profile dev build` will pull each of the base Docker images (`mongo`, `node` and `python`) and build the corresponding apps in development mode on top of them (using `--profile prod` for production deployments).
- `docker compose --profile dev up` will launch a container for each component, such that the web app can be accessed at `localhost:8081`, the server at `localhost:5001` and the database at `localhost:27017`.
- Individual containers can be launched with `docker compose up <service name>` for the services `mongo`, `app`, `app_dev`, `api` and `api_dev`.
- `docker compose stop` will stop all running containers.

## Permanent deployment instructions

There are several steps involved from taking the Docker containers above and provisioning a persistent *datalab* server and instance.
Many of these involve tuning the server configuration for your group following the [additional documentation](config.md) on configuration, but many additional choices also depend on how you plan to host the containers in the long-term.
Some things to consider:

- Typically you will host the app and API containers on the same server behind a reverse proxy such as [NGINX](https://nginx.com). These
- Typically you will need to run the app and API on two different subdomains.
  These can be provided perhaps by an IT department, or by configuring DNS
  settings on your own domain to point to the server

## Note on remote filesystems

This package allows you to attach files from remote filesystems to samples and other entries.
These filesystems can be configured in the config file with the `REMOTE_FILESYSTEMS` option.
In practice, these options should be set in a centralised deployment.


Currently, there are two mechanisms for accessing remote files:

1. You can mount the filesystem locally and provide the path in your datalab config file. For example, for Cambridge Chemistry users, you will have to (connect to the ChemNet VPN and) mount the Grey Group backup servers on your local machine, then define these folders in your config.
2. Access over `ssh`: alternatively, you can set up passwordless `ssh` access to a machine (e.g., using `citadel` as a proxy jump), and paths on that remote machine can be configured as separate filesystems. The filesystem metadata will be synced periodically, and any attached files will be downloaded and stored locally (with the file being kept younger than 1 hour old on each access).
