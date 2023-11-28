# Server configuration and administration

*datalab* has 3 main configuration sources.

1. The Python `ServerConfig` (described below) that allows for *datalab*-specific configuration, such as database connection info, filestore locations and remote filesystem configuration.
    - This can be provided via a JSON or YAML config file at the location provided by the `PYDATALAB_CONFIG_FILE` environment variable, or as environment variables themselves, prefixed with `PYDATALAB_`.
    - The available configuration variables and their default values are listed below.
2. Additional server configuration provided as environment variables, such as secrets like Flask's `SECRET_KEY`, API keys for external services (e.g., Sendgrid) and OAuth client credentials (for logging in via GitHub or ORCID).
    - These can be provided as environment variables or in a `.env` file in the directory from which `pydatalab` is launched.
3. Web app configuration, such as the URL of the relevant *datalab* API and branding (logo URLs, external homepage links).
    - These are typically provided as a `.env` file in the directory from which the webapp is built/served.

## Mandatory settings

There is only one mandatory setting when creating a deployment.
This is the `IDENTIFIER_PREFIX`, which shall be prepended to every entry's refcode to enable global uniqueness of *datalab* entries.
For now, the prefixes themselves are not checked for uniqueness across the fledling *datalab* federation, but will in the future.

This prefix should be set to something relatively short (max 10 chars.) that describes your group or your deployment, e.g., the PI's surname, project ID or department.

This can be set either via a config file, or as an environment variable (e.g., `PYDATALAB_IDENTIFIER_PREFIX='grey'`).
Be warned, if the prefix changes between server launches, all entries will have to be migrated manually to the desired prefix, or maintained at the old prefix.

## User registration & authentication

*datalab* has three supported user registration/authentication
mechanisms:

1. OAuth2 via GitHub accounts that are public members of appropriate GitHub
organizations
2. OAuth2 via ORCID
3. via magic links sent to email addresses

Each is configured differently.

For GitHub, you must register a [GitHub OAuth
application](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app) for your instance, providing the client ID and secret in the `.env` for the API.
Then, you can configure `GITHUB_ORG_ALLOW_LIST` with a list of string IDs of GitHub organizations that user's must be a public member of to register an account.
If this value is set to `None`, then no accounts will be able to register, and if it is set to an empty list, then no restrictions will apply.
You can find the relevant organization IDs using the GitHub API, for example at `https://api.github.com/orgs/<org_name>`.

For ORCID integration, each *datalab* instance must currently register for the ORCID developer program and request new credentials.
As such, this may be tricky to support for new instances.
We are looking for ways around this in the future.

To support sign-in via email magic-links, you must currently provide
additional configuration for the [SendGrid](https://sendgrid.com/) web API, i.e., your default email sender (`MAIL_DEFAULT_SENDER`) and SendGrid API key (`MAIL_PASSWORD`), as environment variables for the API container.
There is currently no restrictions on which email addresses can sign up.
This approach will soon also support using any configured SMTP server.

## Remote filesystems

This package allows you to attach files from remote filesystems to samples and other entries.
These filesystems can be configured in the config file with the `REMOTE_FILESYSTEMS` option.
In practice, these options should be set in a centralised deployment.

Currently, there are two mechanisms for accessing remote files:

1. You can mount the filesystem locally and provide the path in your datalab config file. For example, for Cambridge Chemistry users, you will have to (connect to the ChemNet VPN and) mount the Grey Group backup servers on your local machine, then define these folders in your config.
2. Access over `ssh`: alternatively, you can set up passwordless `ssh` access to a machine (e.g., using `citadel` as a proxy jump), and paths on that remote machine can be configured as separate filesystems. The filesystem metadata will be synced periodically, and any files attached in `datalab` will be downloaded and stored locally on the `pydatalab` server (with the file being kept younger than 1 hour old on each access).

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

# Config API Reference

::: pydatalab.config
