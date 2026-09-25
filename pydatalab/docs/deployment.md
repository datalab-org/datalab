# Deploying *datalab* and server administration

This document will describe the process of manually deploying a *datalab* instance with
Docker and Docker Compose.

!!! warning Consider automated deployments
    Whilst these general instructions may be useful, for a production *datalab* we strongly recommend
    using the [Ansible-based approach](#automated-deployments-with-ansible-and-terraform-recommended).

[Docker](https://docs.docker.com/) uses virtualisation to allow you to build "images" of your software that are transferable and deployable as "containers" across multiple systems.

[Docker Compose](https://docs.docker.com/compose/) is a tool for running
multiple containers as services that can interact with one another.
The `docker-compose.yaml` file in the root of the *datalab* repository describes
how these containers should be built and configured,
Each of the services required by *datalab* (for example, a Python web server running the API, node server for the web UI and a MongoDB database) are isolated into separate containers.

These instructions assume that Docker is installed (a recent version that includes Compose V2 and BuildKit) and that the Docker daemon is running locally.
See the [Docker website](https://docs.docker.com/compose/install/) for instructions for your system.
Note that pulling and building the images can require significant disk space (~5 GB for a full setup), especially when multiple versions of images have been built (you can use `docker system df` to see how much space is being used).

## Automated deployments with Ansible and Terraform (RECOMMENDED)

There are many more advanced tools for provisioning containers and services.
[Terraform](https://www.terraform.io/) or its open source fork
[OpenTofu](https://opentofu.org/) can be used to define and provision cloud resources with
code.
[Ansible](https://www.ansible.com/) can be used to automate the deployment of
containers and configuration to such resources.

Configurations/rules/playbooks for these systems are provided and
maintained for *datalab* and are used in production by many deployments.
They are available with their own instructions at
[datalab-org/datalab-ansible-terraform](https://github.com/datalab-org/datalab-ansible-terraform)
on GitHub.

These automated configurations require a bit more work and understanding, but
can greatly accelerate the deployment process and make it much more
reproducible with additional features such as automatic backups and monitoring.


## Manual deployment with Docker and Docker Compose

Dockerfiles for the web app, server and database can be found in the `.docker` directory.
The production target will copy the state of the repository on build and use `gunicorn` and `serve` to serve the server and app respectively.

There are several steps involved from taking the Docker containers above and provisioning a persistent *datalab* server and instance available through the internet.
Many of these involve tuning the server configuration for your group following the [additional documentation](config.md) on configuration, but many additional choices also depend on how you plan to host the containers in the long-term.
Some things to consider:

- Typically you will host the app and API containers on the same server behind a reverse proxy such as [Nginx](https://nginx.org) (in which case you will need to set the [`BEHIND_REVERSE_PROXY`][pydatalab.config.ServerConfig.BEHIND_REVERSE_PROXY] setting to `True`).
- Typically you will need to run the app and API on two different subdomains.

These can be provided perhaps by an IT department, or by configuring DNS settings on your own domain to point to the server.

You will need to configure the app such so that it points at the relevant hosted API (see [app `.env` description](config.md)), via the `VUE_APP_API_URL` variable.
You can also control other options via several `VUE_APP_*` environment variables listed at the link above.

There will inevitably be specific infrastructure configuration required for your
instance, for example, the mounting of disks into the API container to allow for
saving of files.

These options can be added directly to the `docker-compose.yml` file in your
cloned copy of datalab, with inlined settings providing the location of any local `.env`
files, and config files.

Another more robust approach is to also version control your own *datalab* config.
This can be achieved by creating a new Git repository, adding *datalab* as a
submodule, and then writing a custom `docker-compose.yml` file based on the one
provided with *datalab*.
The process may look something like the following:

- Create a new Git repository on the server to be hosting *datalab*:
  ```shell
  mkdir datalab-deployment; cd datalab-deployment
  git init
  ```

- Add *datalab* as a [Git submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules):
  ```shell
  git submodule add git@github.com:datalab-org/datalab
  cd datalab; git checkout <commit_or_tag>; cd ..  # at this point you can set any tagged version, or just track the main branch
  git commit -a -m "Add datalab as submodule"
  ```

- Use the original docker-compose file as a template and begin tracking it:
  ```shell
  cp docker-compose.yml docker-compose.prod.yml
  git add docker-compose.prod.yml
  git commit -m "Initial docker compose file"
  ```

- Edit the default `docker-compose.yml` file for your needs. To recreate the
  same behaviour as the default definitions, you must first update the build
  "context" to point to your *datalab* submodule. This can be done manually or
  with the one-liner using `sed` (assuming a Linux machine):
  ```shell
  sed -i "s|context: .|context: ./datalab|g" docker-compose.prod.yml
  ```
  Common other updates may be mounting new volumes, or overriding particular
  config variables. An example custom API definition can be found below:
  ```yaml
  api:
    profiles: ["prod"]
    build:
      context: ./datalab
      dockerfile: .docker/server/Dockerfile
      target: production
      args:
        - WEB_CONCURRENCY=16  # increase number of web workers to 16
    depends_on:
      - database
    volumes:
      - ./logs:/logs  # mount a local relative directory for the logs
      - /data/files:/app/files # mount an absolute directory for the data lake
    ports:
      - "5001:5001"
    networks:
      - backend
    environment:
      - PYDATALAB_MONGO_URI=mongodb://database:27017/datalab
      - PYDATALAB_FILES_DIRECTORY=/app/files  # provide the mount point for the file directory
  ```

After this process is complete, the containers can be built and launched with
the familiar commands, with one extra argument pointing to the new
`docker-compose.prod.yml` file:

```shell
docker compose --file docker-compose.prod.yml --profile prod build
docker compose --file docker-compose.prod.yml --profile prod up
```

### Updating a *datalab* instance

As *datalab* is still under active development, it should be desirable to keep up-to-date with the latest features and fixes.
When following the approach above with a Git submodule, it should be as easy as
pulling the latest changes into your submodule, then rebuilding and relaunching the containers, though in some cases it may be that additional config has to be provided in your custom `docker-compose.prod.yml` file.

If not using the above approach, then the process will still be similar.
You must somehow download the latest *datalab* changes to your server (ideally with `git`) and then rebuild and relaunch the relevant Docker containers.

!!! warning Understand the CHANGELOG before updating
    You **should** read the *datalab* CHANGELOG and [release notes](https://github.com/datalab-org/datalab/releases) before deciding to update.
    These may contain specific instructions on required migrations or other steps required in the future that are not covered by this current state
    of the documentation.

!!! danger Backup before updating
    Before performing any updates, make sure you have **multiple redundant copies** of **working** backups of your
    deployment to restore to if anything goes wrong, or if any bugs have been
    introduced in the release process.
    Instructions for this can be found in the [Backups](#backups) section below.

!!! danger Handling database version updates
    The note about backups is especially important for releases that involve a database version update.
    If you are using the automated deployment with Ansible, this should be handled for you automatically, but otherwise,
    you will need to prepare for the upgrade by running `mongodump` with the original database version
    and then `mongorestore` after upgrading.

    If you are unsure, please ask for help on GitHub or Slack before attmepting this.

```shell
cd datalab-deployment/datalab;

# Download all the metadata for released datalab versions
git fetch --tags  

# This one-liner will find the latest released version and check it out
git checkout $(git describe --tags "$(git rev-list --tags --max-count=1)")

# Commit changes to your submodule so that the version is now pinned
cd ..; git commit datalab -m "Updated datalab version"

# Now rebuild any containers and check for errors
docker compose --file docker-compose.prod.yml --profile prod build

# If nothing went wrong, launch the new containers (these will replace any running containers)
docker compose --file docker-compose.prod.yml --profile prod up
```

## Optional JupyterHub tool

JupyterLab is supplied by the independently maintained
[`datalab-jupyter`](https://github.com/Matgenix/datalab-jupyter) component. Its
`[plugin]` extra is installed in the datalab API, while its `[hub]` and
`[server]` extras can run in either the managed image or an independently
administered JupyterHub deployment.

For development, add the Git repository to the root `plugins.toml`:

```toml
dependencies = ["datalab-jupyter[plugin]"]

[tool.uv.sources]
datalab-jupyter = { git = "https://github.com/Matgenix/datalab-jupyter.git" }
```

Run `uv run invoke dev.install` from `pydatalab/`. Production deployments
should use a versioned Git or package source.

If JupyterLab is not needed, do not install `datalab-jupyter` and do not include
the companion Compose file described below. The normal datalab deployment then
creates no Hub container, tools network, Jupyter volume, or Docker-socket mount.

### Compose-managed JupyterHub

Configure matching client credentials in the root environment and explicitly combine the base
Compose file with the companion file supplied by the `datalab-jupyter` repository. Including that
file is what enables the managed Hub; no additional Jupyter profile is needed. Set
`<DATALAB_JUPYTER_CHECKOUT>` to the location of that checkout:

```shell
export DATALAB_JUPYTER_CLIENT_ID=datalab-jupyter
export DATALAB_JUPYTER_CLIENT_SECRET="$(openssl rand -hex 32)"
docker compose -f docker-compose.yml \
  -f <DATALAB_JUPYTER_CHECKOUT>/deployment/docker-compose.datalab.yml \
  --profile prod up --build --wait
docker compose -f docker-compose.yml \
  -f <DATALAB_JUPYTER_CHECKOUT>/deployment/docker-compose.datalab.yml \
  --profile dev up --build --wait
```

Use the same files for later Compose operations, including shutdown:

```shell
docker compose -f docker-compose.yml \
  -f <DATALAB_JUPYTER_CHECKOUT>/deployment/docker-compose.datalab.yml \
  --profile dev down
```

If the companion file is omitted from `down`, Compose does not know about the
Hub service and may leave it running with the tools network still in use.

Production and development profiles are alternatives and should not be run
simultaneously. Docker Compose 2.20 or newer is required for the optional
health-based API dependencies.

The managed Hub binds to `127.0.0.1:8000` by default. For loopback development,
its browser URL is normally `http://localhost:8000/jupyter/`. The bind address
and port can be changed from the shell with
`DATALAB_JUPYTER_BIND_ADDRESS` and `DATALAB_JUPYTER_PORT`.

In production, set `PYDATALAB_APP_URL` to the canonical frontend URL and proxy
its `/jupyter/` path to the Hub, or set
`DATALAB_JUPYTER_PUBLIC_URL` to another browser-facing HTTPS URL. The
reverse proxy must:

- preserve the `/jupyter/` prefix and forwarded host and protocol information;
- proxy HTTP traffic to the Hub on port 8000;
- support WebSocket upgrades and long-lived kernel connections;
- use timeouts appropriate for interactive kernels;
- omit or redact `datalab_launch_code` values from access logs; and
- terminate TLS outside loopback development.

`DATALAB_JUPYTER_PUBLIC_URL` changes the co-deployed Hub's browser-facing
location. `DATALAB_JUPYTER_EXTERNAL_URL` selects a separately administered Hub
instead.

### Security, networking, and storage

The API, Hub, and spawned user servers share a dedicated tools network. Both API
profiles use the `datalab-api` network alias, so notebooks call
`http://datalab-api:5001` regardless of the active profile. MongoDB is not
attached to this network: notebooks must access data through the datalab API and
its current-user permission checks.

DockerSpawner requires the Docker socket to create per-user containers.
Possession of that socket is effectively host-root access, so only the trusted
Hub receives it. User notebook containers receive no Docker socket, MongoDB
credentials, Flask secrets, host bind mounts, or shared client secret. Each
container receives only its user's temporary tool access token, current-user
snapshot, API URL, and persistent work volume.

The managed defaults are:

- 2 CPU cores and 4 GiB of memory per user server;
- shutdown after one hour of inactivity;
- a maximum server age of 24 hours; and
- a persistent work volume keyed by the Compose project and immutable datalab
  user identity.

Override these with `DATALAB_JUPYTER_CPU_LIMIT`,
`DATALAB_JUPYTER_MEM_LIMIT`, `DATALAB_JUPYTER_START_TIMEOUT`,
`DATALAB_JUPYTER_IDLE_TIMEOUT`, and `DATALAB_JUPYTER_MAX_AGE`.

Hub state and encrypted authentication data use a separate persistent volume.
Stopping a user server removes its disposable container while retaining its
work volume. Administrators should define storage quotas and a volume-retention
policy suitable for their deployment.

### Notebook environment

Each Python notebook and Jupyter console preloads:

```python
datalab       # authenticated datalab_api.DatalabClient
current_user  # launch-time identity, role, and group snapshot
```

JupyterLab also contributes **Open in notebook** to the selected-items menus
for Samples, Inventory, Equipment, and items within a collection. Selecting
1–20 rows creates a new notebook with a dedicated kernel and a visible
initialization cell. datalab passes only immutable refcodes; the cell retrieves
the current item dictionaries through the permission-aware API.

The initialization cell runs automatically once when the notebook is created
and defines:

```python
selected_item_refcodes  # ordered immutable refcodes from the table
selected_items          # accessible item dictionaries
selected_item_errors    # refcodes that could not be loaded
```

The cell remains editable and rerunnable. It is not executed automatically
after a kernel restart or when the notebook is later opened with a fresh
kernel. A normal JupyterLab launch from the Tools menu does not create a
notebook and does not define these selection-specific variables.

The managed image includes SciPy, pandas, Matplotlib, seaborn, ipywidgets,
lmfit, uncertainties, Pint, openpyxl, h5py, and tqdm. NumPy is installed as a
dependency and constrained for compatibility with the pinned `datalab-api`
client.

### External JupyterHub

Set `DATALAB_JUPYTER_EXTERNAL_URL` to use an independently deployed
Hub. In that case, run the normal base Compose file without
the `datalab-jupyter` companion Compose file; no local Hub is created. The external
administrator owns TLS, proxying, availability, spawning, storage, quotas,
culling, and the user-server image.

Install `datalab-jupyter[hub]` in the external Hub and
`datalab-jupyter[server]` in its user image, then configure the matching datalab
API URL, client ID, and client secret. The integration
exchanges a single-use launch code for a temporary current-user tool access
token and passes it only to that user's notebook container. The external
administrator must keep user-server lifetimes within the token lifetime and
must isolate notebook containers from datalab's database and server secrets.

New datalab users are created dynamically in JupyterHub at their first
successful launch; the Hub does not need to be restarted or given a
pre-provisioned user list.


## General server administration

Currently most administration tasks must be handled directly inside the Python API container.
Several helper routines are available as `invoke` tasks in `tasks.py` in the `pydatalab` root folder.
You can list all available tasks by running `invoke --list` in the root `pydatalab` folder after installing the package with the `dev` extras (e.g., `uv sync --dev`).
In the future, many admin tasks (e.g., updating user info, allowing/blocking user accounts, defining subgroups) will be accessible in the web UI.

### Importing chemical inventories

One such `invoke` task implements the ingestion of a [ChemInventory](https://cheminventory.net) chemical inventory into *datalab*.
It relies on the Excel export feature of ChemInventory and is achieved with `invoke admin.import-cheminventory <filename>`.
If a future export is made and reimported, the old entries will be kept and updated, rather than overwritten.
*datalab* currently has no functionality for chemical inventory management itself; if you wish to support importing from another inventory system, please [raise an issue](https://github.com/datalab-org/datalab/issues/new).

If a two-way or realtime sync with ChemInventory is desired, this can be
achieved with the [`datalab-cheminventory-plugin`](https://github.com/datalab-industries/datalab-cheminventory-plugin).

### Backups

!!! warning Robust offsite encrypted backups with Borg
    We strongly recommend following the instructions in the [`datalab-ansible-terraform` repository](https://github.com/datalab-industries/datalab-ansible-terraform#backups)
    that encourage the use of [Borg](https://www.borgbackup.org/) for encrypted, incremental and compressed backups of the database and filestore with the ability to roll
    back to particular snapshot versions easily.

#### Native snapshot backups

*datalab* provides a simple native way to configure and create a snapshot backups of the database and filestore.
The option [`BACKUP_STRATEGIES`][pydatalab.config.ServerConfig.BACKUP_STRATEGIES] allows you to list strategies for scheduled backups, with their frequency, storage location (can be local or remote) and retention.
These backups are only performed when scheduled externally (e.g., via `cron` on the hosting server), or when triggered manually using the `invoke admin.create-backup` task.

The simplest way to create a backup is to run `invoke admin.create-backup --output-path /tmp/backup.tar.gz`, which will create a compressed backup.
This should be run from the server or container for the API, and will make use of the config to connect to the database and file store.
This approach will not follow any retention strategy.

Alternatively, you can create a backup given the strategy name defined in the server config, using the same task:

```
invoke admin.create-backup --strategy-name daily-snapshots
```

This will apply the retention strategy and any copying to remote resources as configured.

When scheduling backups externally, it is recommended you do not use `cron` inside the server Docker container.
Instead, you could schedule a job that calls, for example:

```shell
#              <container name>          <invoke task name>            <configured strategy name>
#                    ^                           ^                                  ^
docker compose exec api uv run invoke admin.create-backup --strategy-name daily-snapshots
```

Care must be taken to schedule this command to run from the correct directory.
