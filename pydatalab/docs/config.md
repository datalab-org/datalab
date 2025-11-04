# Server configuration

This document describes the different options for configuring a *datalab*
instance.
It is primarily intended for those who are *deploying* *datalab* on persistent
hardware, but may also be useful for developers.
Deployment instructions can be found under ["Deploying datalab and server
administration"](deployment.md).

*datalab* has 3 main configuration sources.

1. The Python [`ServerConfig`][pydatalab.config.ServerConfig] (described below) that allows for *datalab*-specific configuration, such as database connection info, filestore locations and remote filesystem configuration.
.
    - This can be provided via a JSON or YAML config file at the location provided by the `PYDATALAB_CONFIG_FILE` environment variable, or as environment variables themselves, prefixed with `PYDATALAB_`. The available configuration variables and their default values are listed below.
2. Additional server configuration provided as environment variables, such as secrets like the Flask server's [`SECRET_KEY`][pydatalab.config.ServerConfig.SECRET_KEY], API keys for external services (e.g., SMTP `MAIL_PASSWORD`) and OAuth client credentials (for logging in via GitHub or ORCID).
These can be provided as either:
    - environment variables with the appropriate `FLASK_` or `PYDATALAB_` prefix (for options that are also in the config model from option 1.)
    - an `.env` file in the directory from which `pydatalab` is launched (NB: here, the `FLASK_` prefix is not required, but any options present in the pydatalab config must still have the `PYDATALAB_` prefix).
3. Web app configuration, such as the URL of the relevant *datalab* API and branding (logo URLs, external homepage links).
    - These are typically provided as a `.env` file in the directory from which the webapp is built/served.
    - The main options include (a full list can be found in the `docker-compose.yml` file):
        - `VUE_APP_API_URL`: the URL of the *datalab* API, which is used by the web app to communicate with the server.
        - `VUE_APP_LOGO_URL`: the URL of an image to use as the logo header in the web app.
        - `VUE_APP_HOMEPAGE_URL`: a URL to provide as a link from the web app header.
        - `VUE_APP_EDITABLE_INVENTORY`: whether the inventory can be edited by non-admin users in the web app.
        - `VUE_APP_WEBSITE_TITLE`: the title of the web app, which is displayed in the browser tab and header.
        - `VUE_APP_QR_CODE_RESOLVER_URL`: the URL of a service that can resolve QR codes to *datalab* entries, which is used by the web app to display QR codes for entries (see [datalab-org/datalab-purl](https://github.com/datalab-org/datalab-purl) for more information).
        - `VUE_APP_AUTOMATICALLY_GENERATE_ID_DEFAULT`: whether to automatically generate IDs for new entries in the web app by default, or require a checkbox to be ticked at item creation.

> [!NOTE]
> The possible ways to set configuration options can be inconsistent with each other, e.g., values required to be `None` in Python should be set to `null` in the JSON config file and as .env values. Similarly, boolean values may be set to `true` or `false` in the JSON config file, but can be set to {`1`, `yes`, `true`} or {`0`, `no`, `false`} in a `.env` file.

## Mandatory settings

There is only one mandatory setting when creating a deployment.
This is the [`IDENTIFIER_PREFIX`][pydatalab.config.ServerConfig.IDENTIFIER_PREFIX], which shall be prepended to every entry's refcode to enable global uniqueness of *datalab* entries.
For now, the prefixes themselves are not checked for uniqueness across the fledgling *datalab* federation, but will in the future.

This prefix should be set to something relatively short (max 10 chars.) that describes your group or your deployment, e.g., the PI's surname, project ID or department.

This can be set either via a config file, or as an environment variable (e.g., `PYDATALAB_IDENTIFIER_PREFIX='grey'`).
Be warned, if the prefix changes between server launches, all entries will have to be migrated manually to the desired prefix, or maintained at the old prefix.

## User registration & authentication

*datalab* has three supported user registration/authentication
mechanisms:

1. OAuth2 via [GitHub](https://github.com) accounts that are public members of appropriate GitHub organizations
2. OAuth2 via [ORCID](https://orcid.org)
3. via magic links sent to email addresses

Each is configured differently.
If left unconfigured, then the corresponding registration mechanism will not be available to the user.

#### GitHub OAuth2

For GitHub, you must register a [GitHub OAuth
application](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app) for your instance, providing the client ID and secret in the `.env` for the API, using the variable names `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET`.
These should be provided in a `.env` file local to your app and not added to your main config file.

The authorization callback URL in the GitHub app settings should be set to `<YOUR_API_URL>/login/github/authorized`.
A user's first login may direct them to this page rather than the web app, depending on their browser.
The user will then simply have to navigate back to the URL of the web app, where they should find themselves to be logged in.

Then, you can configure [`GITHUB_ORG_ALLOW_LIST`][pydatalab.config.ServerConfig.GITHUB_ORG_ALLOW_LIST] with a list of string IDs of GitHub organizations that user's must be a public member of to register an account.
If this value is set to `None`, then any GitHub account will be able to register, and if it is set to an empty list, then no accounts will be able to register.
You can find the relevant organization IDs using the GitHub API, for example at `https://api.github.com/orgs/<org_name>`.

#### ORCID OAuth2

For [ORCID](https://orcid.org) integration, each *datalab* instance must currently register for the ORCID developer program and request new credentials for their public API.
These credentials can then be provided via the `ORCID_OAUTH_CLIENT_ID` and `ORCID_OAUTH_CLIENT_SECRET` environment variables, in the same way as the GitHub settings above.
Currently, only users with existing *datalab* accounts can connect their ORCIDs, but in future new users will be able to register for a *datalab* instance via ORCID, with an admin required to validate their registration.

#### Email magic links

To support sign-in via email magic-links, you must currently provide additional configuration for authorized SMTP server.
The SMTP server must be configured via the settings [`EMAIL_AUTH_SMTP_SETTINGS`][pydatalab.config.ServerConfig.EMAIL_AUTH_SMTP_SETTINGS], with expected values `MAIL_SERVER`, `MAIL_USER`, `MAIL_DEFAULT_SENDER`, `MAIL_PORT` and `MAIL_USE_TLS`, following the environment variables described in the [Flask-Mail documentation](https://flask-mail.readthedocs.io/en/latest/#configuring-flask-mail).
The `MAIL_PASSWORD` setting should then be provided via a `.env` file.

Third-party options with a free tier include [resend](https://resend.com/), which can be configured to use an appropriate API key, after verifying ownership of the `MAIL_DEFAULT_SENDER` address via DNS (see [resend](https://resend.com/docs/dashboard/domains/introduction) for an example configuration).

The email addresses that are allowed to sign up can be restricted by domain/subdomain using the [`EMAIL_DOMAIN_ALLOW_LIST`][pydatalab.config.ServerConfig.EMAIL_DOMAIN_ALLOW_LIST] setting.

## Remote filesystems

This package allows you to attach files from remote filesystems to samples and other entries.
These filesystems can be configured in the config file with the [`REMOTE_FILESYSTEMS`][pydatalab.config.ServerConfig.REMOTE_FILESYSTEMS] option.
In practice, these options should be set in a centralised deployment.

Currently, there are two mechanisms for accessing remote files:

1. You can mount the filesystem locally and provide the path in your datalab config file. For example, for Cambridge Chemistry users, you will have to (connect to the ChemNet VPN and) mount the Grey Group backup servers on your local machine, then define these folders in your config.
2. Access over SSH: alternatively, you can set up passwordless `ssh` access to a machine (e.g., using `citadel` as a proxy jump), and paths on that remote machine can be configured as separate filesystems. The filesystem metadata will be synced periodically, and any files attached in `datalab` will be downloaded and stored locally on the `pydatalab` server (with the file being kept younger than 1 hour old on each access).


## Config API Reference

::: pydatalab.config.ServerConfig
    options:
      heading_level: 2
      show_root_heading: true
      show_source: false

::: pydatalab.config.RemoteFilesystem
    options:
      heading_level: 2
      show_root_heading: true
      show_source: false

::: pydatalab.config.SMTPSettings
    options:
      heading_level: 2
      show_root_heading: true
      show_source: false

::: pydatalab.config.DeploymentMetadata
    options:
      heading_level: 2
      show_root_heading: true
      show_source: false
