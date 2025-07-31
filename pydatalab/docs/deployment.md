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
      dockerfile: .docker/server_dockerfile
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
