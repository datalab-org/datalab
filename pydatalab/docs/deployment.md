# Deploying *datalab* and server administration

This document will describe the process of deploying a *datalab* instance with
Docker and Docker Compose.
As well as deploying a production *instance*, this approach can be useful for creating a consistent development environment that will
closely match the deployed system.

[Docker](https://docs.docker.com/) uses virtualization to allow you to build "images" of your software that are transferrable and deployable as "containers" across multiple systems.

[Docker Compose](https://docs.docker.com/compose/) is a tool for running
multiple containers as services that can interact with one another.
The `docker-compose.yaml` file in the root of the *datalab* repository describes
how these containers should be built and configured,
Each of the services required by *datalab* (for example, a Python web server running the API, node server for the web UI and a MongoDB database) are isolated into separate containers.

These instructions assume that Docker is installed (a recent version that includes Compose V2 and BuildKit) and that the Docker daemon is running locally.
See the [Docker website](https://docs.docker.com/compose/install/) for instructions for your system.
Note that pulling and building the images can require significant disk space (~5 GB for a full setup), especially when multiple versions of images have been built (you can use `docker system df` to see how much spaace is being used).

## Automated provisioning and deployments

There are many more advanced tools for provisioning containers and services.
[Terraform](https://www.terraform.io/) or its open source fork
[OpenTofu](https://opentofu.org/) can be used to define and provision cloud resources with
code.
[Ansible](https://www.ansible.com/) can be used to automate the deployment of
containers and configuration to such resources.

Configurations/rules/playbooks for these systems have been written for *datalab*
and are used in production by many deployments.
They are available with their own instructions at
[datalab-org/datalab-ansible-terraform](https://github.com/datalab-org/datalab-ansible-terraform)
on GitHub.

These automated configurations require a bit more work and understanding, but
can greatly accelerate the deployment process and make it much more
reproducible.


## Deployment with Docker and Docker Compose

Dockerfiles for the web app, server and database can be found in the `.docker` directory.
There are separate build targets for `production` and `development` (and corresponding docker-compose profiles `prod` and `dev`).

- The production target will copy the state of the repository on build and use `gunicorn` and `serve` to serve the server and app respectively.
- The development target mounts the repository in the running container and provides hot-reloading servers for both the backend and frontend.

### Development environment

The following shell snippets will download *datalab* and launch containers on the machine in which they are executed.

Clone and enter the repository, if not done already

```shell
git clone git@github.com:the-grey-group/datalab; cd datalab
```

Build the development containers:

```shell
docker compose --profile dev build
```

Launch the containers: any local changes made to code in the repository will be loaded by the running containers.

```shell
docker compose --profile dev up
```

Once the launch has completed (can take a couple of minutes), the web app and API will be accessible at http://localhost:8081 and http://localhost:5001, respectively.
Your shell will be left "attached" to the container logs, ending the process in
your terminal (e.g., CTRL-C or otherwise) will kill the containers, but simply
closing the terminal will leave the containers running.
To stop the containers, you can run:

```shell
docker compose --profile dev down
```

## Permanent deployment instructions

There are several steps involved from taking the Docker containers above and provisioning a persistent *datalab* server and instance available through the internet.
Many of these involve tuning the server configuration for your group following the [additional documentation](config.md) on configuration, but many additional choices also depend on how you plan to host the containers in the long-term.
Some things to consider:

- Typically you will host the app and API containers on the same server behind a reverse proxy such as [Nginx](https://nginx.org) (in which case you will need to set the [`BEHIND_REVERSE_PROXY`][pydatalab.config.ServerConfig.BEHIND_REVERSE_PROXY] setting to `True`).
- Typically you will need to run the app and API on two different subdomains.

These can be provided perhaps by an IT department, or by configuring DNS settings on your own domain to point to the server.
You will need to configure the app such so that it points at the relevant hosted API (see [app `.env` description](config.md#app).

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
  git submodule add git@github.com:the-grey-group/datalab
  cd datalab; git checkout v0.4.0  # at this point you can set any default version, or just track the main branch
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
    You **should** read the *datalab* CHANGELOG and [release notes](https://github.com/the-grey-group/datalab/releases) before deciding to update.
    These may contain specific instructions on required migrations or other steps required in the future that are not covered by this current state
    of the documentation.

!!! danger Backup before updating
    Before performing any updates, make sure you have **multiple redundant copies** of **working** backups of your
    deployment to restore to if anything goes wrong, or if any bugs have been
    introduced in the release process.
    Instructions for this can be found in the [Backups](#backups) section below.

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


## General Server administration

Currently most administration tasks must be handled directly inside the Python API container.
Several helper routines are available as `invoke` tasks in `tasks.py` in the `pydatalab` root folder.
You can list all available tasks by running `invoke --list` in the root `pydatalab` folder after installing the package with the `[dev]` extras.
In the future, many admin tasks (e.g., updating user info, allowing/blocking user accounts, defining subgroups) will be accessible in the web UI.

### Importing chemical inventories

One such `invoke` task implements the ingestion of a [ChemInventory](https://cheminventory.net) chemical inventory into *datalab*.
It relies on the Excel export feature of ChemInventory and is achieved with `invoke admin.import-cheminventory <filename>`.
If a future export is made and reimported, the old entries will be kept and updated, rather than overwritten.
*datalab* currently has no functionality for chemical inventory management itself; if you wish to support importing from another inventory system, please [raise an issue](https://github.com/the-grey-group/datalab/issues/new).

### Backups

*datalab* provides a way to configure and create a snapshot backups of the database and filestore.
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
docker compose exec api invoke pipenv run admin.create-backup --strategy-name daily-snapshots
```

Care must be taken to schedule this command to run from the correct directory.

In the future, this may be integrated directly into the *datalab* server using a Python-based scheduler.
