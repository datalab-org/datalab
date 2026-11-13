# Server configuration

This document describes the different options for configuring a *datalab*
instance.
It is primarily intended for those who are *deploying* *datalab* on persistent
hardware, but may also be useful for developers.
Deployment instructions can be found under ["Deploying datalab and server
administration"](deployment.md).

*datalab* has 3 main configuration sources.

1. The Python [`ServerConfig`][pydatalab.config.ServerConfig] (described below) that allows for *datalab*-specific configuration, such as database connection info, filestore locations and remote filesystem configuration.
    - This can be provided via a JSON or YAML config file at the location provided by the `PYDATALAB_CONFIG_FILE` environment variable, or as environment variables themselves, prefixed with `PYDATALAB_`. The available configuration variables and their default values are listed below.
2. Additional server configuration provided as environment variables, such as secrets like the Flask server's [`SECRET_KEY`][pydatalab.config.ServerConfig.SECRET_KEY], API keys for external services (e.g., SMTP `MAIL_PASSWORD`) and OAuth client credentials (for logging in via GitHub, ORCID, etc.).
These can be provided as either:
    - environment variables with the appropriate `FLASK_` or `PYDATALAB_` prefix (for options that are also in the config model from option 1.)
    - an `.env` file in the directory from which `pydatalab` is launched (NB: here, the `FLASK_` prefix is not required, but any options present in the pydatalab config must still have the `PYDATALAB_` prefix).
3. Web app configuration, such as the URL of the relevant *datalab* API and branding (logo URLs, external homepage links).
    - These are typically provided as a `.env` file in the directory from which the webapp is built/served.
    - In the production Docker image they are instead read from the container's environment each time it starts, so changing them only requires recreating the container, not rebuilding the image. They are written to a `config.js` that is served publicly, so must never contain secrets.
    - All settings are described in `webapp/src/config.schema.json`. The production container refuses to start if a value does not match this schema, and logs a warning for unknown `VUE_APP_*` variables. Elsewhere, invalid values are reported in the browser console.
    - The main options include (a full list can be found in `webapp/src/config.schema.json`):
        - `VUE_APP_API_URL`: the URL of the *datalab* API, which is used by the web app to communicate with the server.
        - `VUE_APP_LOGO_URL`: the URL of an image to use as the logo header in the web app.
        - `VUE_APP_HOMEPAGE_URL`: a URL to provide as a link from the web app header, and as a button on the dedicated login page.
        - `VUE_APP_EDITABLE_INVENTORY`: whether the inventory can be edited by non-admin users in the web app.
        - `VUE_APP_HIDE_COLLECTIONS`: whether to hide collection pages and controls in the web app. This defaults to `false`. It is not an access-control mechanism and does not disable collection API routes or alter stored collection data.
        - `VUE_APP_WEBSITE_TITLE`: the title of the web app, which is displayed in the browser tab and header. It is also used in the heading of the dedicated login page, as "Welcome to the `<title>`".
        - `VUE_APP_QR_CODE_RESOLVER_URL`: the URL of a service that can resolve QR codes to *datalab* entries, which is used by the web app to display QR codes for entries (see [datalab-org/datalab-purl](https://github.com/datalab-org/datalab-purl) for more information).
        - `VUE_APP_AUTOMATICALLY_GENERATE_ID_DEFAULT`: whether to automatically generate IDs for new entries in the web app by default, or require a checkbox to be ticked at item creation.

> [!NOTE]
> The possible ways to set configuration options can be inconsistent with each other, e.g., values required to be `None` in Python should be set to `null` in the JSON config file and as .env values. Similarly, boolean values may be set to `true` or `false` in the JSON config file, but can be set to {`1`, `yes`, `true`} or {`0`, `no`, `false`} in a `.env` file.

Nested core settings use a double underscore in environment-variable names.
For example, `TOOLS.DISABLED` becomes `PYDATALAB_TOOLS__DISABLED`.

When the frontend and API use different non-loopback origins, set
`PYDATALAB_APP_URL` to the canonical frontend URL.
The tool launch endpoint treats this URL as its trusted browser origin.
Use HTTPS for this URL outside loopback development and testing.

## Tools

Installed external tool plugins are enabled by default, for both standalone and
in-app UI kinds.
Disable selected plugins with the `TOOLS.DISABLED` set:

```shell
PYDATALAB_TOOLS__DISABLED='["example-tool", "another-tool"]'
```

Set `TOOLS.ORDER` to place selected tools in a preferred order across the
navigation menu, Tools page, and selected-items actions:

```shell
PYDATALAB_TOOLS__ORDER='["jupyter", "item-comparison"]'
```

The setting uses stable tool IDs rather than display names. Listed, available
tools appear first in the configured order. Installed tools omitted from the
list follow in alphabetical ID order. Unknown, unavailable, disabled, or
uninstalled IDs are ignored, allowing the same partial order to be shared by
deployments with different plugin sets. Duplicate IDs are invalid.

JupyterLab is supplied by the separately installed
[`datalab-jupyter`](https://github.com/Matgenix/datalab-jupyter) tool plugin.
Its settings are owned by that package rather than `ServerConfig`:

```shell
export DATALAB_JUPYTER_CLIENT_ID=datalab-jupyter
export DATALAB_JUPYTER_CLIENT_SECRET="$(openssl rand -hex 32)"
```

For a Compose `.env` file, run `openssl rand -hex 32` separately and paste its
literal output as the value; dotenv files do not execute shell substitutions.

Set `DATALAB_JUPYTER_EXTERNAL_URL` to the browser-facing URL of an independently
managed Hub. `DATALAB_JUPYTER_PUBLIC_URL` optionally overrides the co-deployed
Hub URL. The client secret must contain at least 32 characters and be shared
only with the corresponding Hub. Installation enables the plugin; use the
generic `TOOLS.DISABLED` setting to disable it.
See [Tools](tools.md) for a general introduction and
[JupyterHub deployment](deployment.md#optional-jupyterhub-tool) for runtime,
network, and security details.

## Mandatory settings

There is only one mandatory setting when creating a deployment.
This is the [`IDENTIFIER_PREFIX`][pydatalab.config.ServerConfig.IDENTIFIER_PREFIX], which shall be prepended to every entry's refcode to enable global uniqueness of *datalab* entries.
For now, the prefixes themselves are not checked for uniqueness across the fledgling *datalab* federation, but will in the future.

This prefix should be set to something relatively short (max 10 chars.) that describes your group or your deployment, e.g., the PI's surname, project ID or department.

This can be set either via a config file, or as an environment variable (e.g., `PYDATALAB_IDENTIFIER_PREFIX='grey'`).
Be warned, if the prefix changes between server launches, all entries will have to be migrated manually to the desired prefix, or maintained at the old prefix.

## Item and block availability

Deployments can restrict which data block types users may add with
[`BLOCK_TYPE_ALLOW_LIST`][pydatalab.config.ServerConfig.BLOCK_TYPE_ALLOW_LIST].
The values are the exact, case-sensitive `blocktype` slugs declared by the block classes, not
their display names. Built-in and plugin-provided blocks use the same registry and are configured
in the same way. For example:

```json
{
  "BLOCK_TYPE_ALLOW_LIST": ["comment", "media", "xrd", "my-plugin-block"]
}
```

The equivalent environment variable is a JSON list:

```bash
export PYDATALAB_BLOCK_TYPE_ALLOW_LIST='["comment", "media", "xrd", "my-plugin-block"]'
```

The default value, `null`/`None`, makes every installed block type available. An empty list
prevents users from adding any new blocks. Unknown slugs are ignored with a warning during server
startup, which allows temporarily missing plugins without preventing the deployment from starting.

Changing the allowlist does not remove or disable blocks that are already stored. Existing blocks
remain viewable, editable, and deletable; the setting only controls which types may be added after
the restriction is applied. While either this setting or `ITEM_TYPE_ALLOW_LIST` is configured, new
blocks of a type that is not installed are also rejected, rather than stored as unsupported blocks.

Deployments can also restrict which item types users may create, and optionally narrow the blocks
that may be added to each item type, with
[`ITEM_TYPE_ALLOW_LIST`][pydatalab.config.ServerConfig.ITEM_TYPE_ALLOW_LIST]. Entries can be either
an item type name or an object containing a `type` and `block_type_allow_list`:

```json
{
  "ITEM_TYPE_ALLOW_LIST": [
    "samples",
    {
      "type": "cells",
      "block_type_allow_list": ["comment", "cycle"]
    },
    {
      "type": "equipment",
      "block_type_allow_list": []
    }
  ]
}
```

A string entry allows that item type to use every block permitted by the global
`BLOCK_TYPE_ALLOW_LIST`. An object entry restricts new blocks to the intersection of its
`block_type_allow_list` and the global list. An empty nested list allows creating the item type but
prevents adding blocks to it.

The equivalent environment variable is a JSON list:

```bash
export PYDATALAB_ITEM_TYPE_ALLOW_LIST='["samples", {"type": "cells", "block_type_allow_list": ["comment", "cycle"]}]'
```

The default value, `null`/`None`, allows every registered item type with no additional per-type
block restriction. An empty top-level list prevents creating any new items or blocks. When the
setting is present, item types omitted from it cannot be created and existing items of those types
cannot receive new blocks. Duplicate item type entries are invalid because their block policy
would be ambiguous.

Item names and block slugs are exact and case-sensitive. Built-in and plugin-provided types use the same
registries; custom item types must use their complete `<namespace>:<type-name>` identifier. Unknown types produce a startup warning and are ignored.

These settings only control creation. Existing restricted items and blocks remain viewable,
editable, saveable, deletable, exportable, and restorable, so changing deployment policy does not
require a database migration.

## User registration & authentication

*datalab* has two supported user registration/authentication
mechanisms:

1. OAuth2 via an OAuth provider like [GitHub](https://github.com), [ORCID](https://orcid.org) or Google and Microsoft.
2. via magic links sent to email addresses

Each is configured differently.
If left unconfigured, then the corresponding registration mechanism will not be available to the user.

Any of these methods can be restricted to logging in to (or connecting to) existing accounts, without allowing new registrations, via [`LOGIN_ONLY_AUTH_METHODS`][pydatalab.config.ServerConfig.LOGIN_ONLY_AUTH_METHODS], e.g., `["email", "github", "google", "microsoft"]` to require users to register with their ORCID first.
The domain and organisation allow lists described below only apply to new registrations; existing users can always log in.

### Email magic links

To support sign-in via email magic-links, you must currently provide additional configuration for authorized SMTP server.
The SMTP server must be configured via the settings [`EMAIL_AUTH_SMTP_SETTINGS`][pydatalab.config.ServerConfig.EMAIL_AUTH_SMTP_SETTINGS], with expected values `MAIL_SERVER`, `MAIL_USER`, `MAIL_DEFAULT_SENDER`, `MAIL_PORT` and `MAIL_USE_TLS`, following the environment variables described in the [Flask-Mail documentation](https://flask-mail.readthedocs.io/en/latest/#configuring-flask-mail).
The `MAIL_PASSWORD` setting should then be provided via a `.env` file.

Third-party options with a free tier include [resend](https://resend.com/), which can be configured to use an appropriate API key, after verifying ownership of the `MAIL_DEFAULT_SENDER` address via DNS (see [resend](https://resend.com/docs/dashboard/domains/introduction) for an example configuration).

The email addresses that are allowed to sign up can be restricted by domain/subdomain using the [`EMAIL_DOMAIN_ALLOW_LIST`][pydatalab.config.ServerConfig.EMAIL_DOMAIN_ALLOW_LIST] setting.

If SMTP settings are required for notification emails but email magic-link sign-in should be disabled, set [`DISABLE_MAGIC_LINK_AUTH`][pydatalab.config.ServerConfig.DISABLE_MAGIC_LINK_AUTH] to `true`.
This hides email authentication from the advertised authentication mechanisms and rejects direct requests to generate or consume magic links.

### OAuth2

OAuth2 allows users to log in using their existing accounts with third-party providers, without the need for a password.
Generally, you register an application with the provider, which gives you a client ID and secret that you can use to configure the OAuth2 settings in *datalab*.

When the dedicated login page is enabled, the web app preserves the requested internal page through the external OAuth flow and returns the user to it after login.
This redirect uses [`APP_URL`][pydatalab.config.ServerConfig.APP_URL] as the trusted web app origin, so `APP_URL` must be configured correctly.

Each provider then has bespoke settings to control the permissions that accounts registered via the external provider will have.

For developers, if you are testing locally without HTTPS, you must also set `OAUTHLIB_INSECURE_TRANSPORT=1` and `OAUTHLIB_RELAX_TOKEN_SCOPE=1` in your environment to circumvent security requirements; this should not be used in production.

> [!NOTE]
> A common user confusion occurs when they register an account via an OAuth provider, but then try to log in via email magic link (or vice versa) (or via another OAuth provider).
> These accounts will not be associated with each other, so the user will end up with multiple accounts that they have to log in to separately.
> Admins can merge the accounts manually, or simply delete the duplicates and ask the user to login via the appropriate method before trying to connect the other external account.

#### GitHub OAuth2

For GitHub, you must register a [GitHub OAuth
application](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app) for your instance, providing the client ID and secret in the `.env` for the API, using the variable names `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET`.
These should be provided in a `.env` file local to your app and not added to your main config file.

The authorization callback URL in the GitHub app settings should be set to `<YOUR_API_URL>/login/github/authorized`.

Then, you can configure [`GITHUB_ORG_ALLOW_LIST`][pydatalab.config.ServerConfig.GITHUB_ORG_ALLOW_LIST] with a list of string IDs of GitHub organizations that user's must be a public member of to register an account.
If this value is set to `None`, then any GitHub account will be able to register, and if it is set to an empty list, then no accounts will be able to register.
You can find the relevant organization IDs using the GitHub API, for example at `https://api.github.com/orgs/<org_name>`.

#### Google OAuth2

For Google, you must register a [Google OAuth 2.0 Client](https://developers.google.com/identity/protocols/oauth2/web-server) in the Google Cloud Console for your instance.
You need to provide the client ID and secret in the `.env` file for the API using the variable names `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`.

The Authorized redirect URI in the Google Cloud settings must be set to `<YOUR_API_URL>/login/google/authorized`.

You can restrict registration to specific email domains using the [`EMAIL_DOMAIN_ALLOW_LIST`][pydatalab.config.ServerConfig.EMAIL_DOMAIN_ALLOW_LIST] setting.
If this is set to `None` or `null`, any user with a Google account can register.

#### Microsoft OAuth2

For Microsoft (Azure AD), you must register an [Azure App Registration](https://learn.microsoft.com/en-us/entra/identity-platform/v2-app-types#web-apps) for your instance, providing the client ID and secret in the `.env` for the API, using the variable names `MICROSOFT_OAUTH_CLIENT_ID` and `MICROSOFT_OAUTH_CLIENT_SECRET`.
These should be provided in a `.env` file local to your app and not added to your main config file.

The redirect URI in the Azure app settings should be set to `<YOUR_API_URL>/login/microsoft/authorized`. When creating the credentials in the Azure Portal, ensure you navigate to "Certificates & secrets" and copy the **Value** of the client secret, as the "Secret ID" cannot be used for authentication.

By default, any Microsoft account (work, school, or personal) can be used to register if the application is configured as "Multi-tenant" in Azure.

#### ORCID OAuth2

For [ORCID](https://orcid.org) integration, each *datalab* instance must currently register for the ORCID developer program and request new credentials for their public API.
These credentials can then be provided via the `ORCID_OAUTH_CLIENT_ID` and `ORCID_OAUTH_CLIENT_SECRET` environment variables, in the same way as the GitHub settings above.

## Remote filesystems

This package allows you to attach files from remote filesystems to samples and other entries.
These filesystems can be configured in the config file with the [`REMOTE_FILESYSTEMS`][pydatalab.config.ServerConfig.REMOTE_FILESYSTEMS] option.
In practice, these options should be set in a centralised deployment.

Currently, there are two mechanisms for accessing remote files:

1. You can mount the filesystem locally and provide the path in your datalab config file. For example, for Cambridge Chemistry users, you will have to (connect to the ChemNet VPN and) mount the Grey Group backup servers on your local machine, then define these folders in your config.
2. Access over SSH: alternatively, you can set up passwordless `ssh` access to a machine (e.g., using `citadel` as a proxy jump), and paths on that remote machine can be configured as separate filesystems. The filesystem metadata will be synced periodically, and any files attached in `datalab` will be downloaded and stored locally on the `pydatalab` server (with the file being kept younger than 1 hour old on each access).

## Customisation and branding

Deployments can customise the look and feel of their *datalab* instance by providing files under a `public/custom/` directory in the web app.
This directory can be a symlink to a folder in your deployment repository, or mounted as a volume in Docker.
It should be made available at `webapp/public/custom/` relative to the *datalab* source tree.

When building the production Docker image, static files in this directory are only added to the final image, so changing them does not rebuild the app; they can also be mounted at `/app/dist/custom` in the running container.
Custom components (`public/custom/components/`) are compiled into the app, so changing them does require a rebuild.
Only `components/` is available when they are compiled, so custom components must use absolute URLs for other files in `public/custom/` (e.g., `/custom/logos/mylogo.png`), rather than relative imports (e.g., `../logos/mylogo.png`), which will fail the build.

The following customisations are supported:

### CSS overrides (`public/custom/override.css`)

A CSS file that is loaded globally before the app styles, allowing you to override any default styling.
Common uses include setting a custom font, accent colours, or other branding tweaks.
If this file does not exist, it is silently ignored.

For example, to set a custom font globally:

```css
@font-face {
  font-family: "My Custom Font";
  src: url("fonts/MyCustomFont-Regular.woff2") format("woff2");
  font-weight: 400;
}

:root {
  --custom-font-family: "My Custom Font";
}

#app {
  font-family: var(--custom-font-family), sans-serif;
}
```

### Custom fonts (`public/custom/fonts/`)

Place font files (`.woff2`, `.ttf`, etc.) in this directory and reference them from `override.css` using relative paths (e.g., `url("fonts/MyFont.woff2")`).

### Custom logos (`public/custom/logos/`)

Place logo images in this directory.
They can be referenced from custom components or CSS using absolute paths (e.g., `/custom/logos/mylogo.png`).

The main instance logo can also be customised via the `VUE_APP_LOGO_URL` environment variable, which accepts a path relative to the `public/` directory.

### Custom about page (`public/custom/components/CustomAbout.vue`)

Deployments can provide a custom Vue component that will be displayed in a collapsible panel on the About page.
Place a `CustomAbout.vue` file in `public/custom/components/` and it will automatically replace the default empty skeleton at build time (via webpack's `NormalModuleReplacementPlugin`).

The component can contain any valid Vue template, script and scoped styles.
No special configuration or flags are needed — if the file exists, it will be used.

### Custom login page content (`public/custom/components/CustomLoginInfo.vue`)

Deployments can provide a custom Vue component for the content of the login box.
Place a `CustomLoginInfo.vue` file in `public/custom/components/` and it will automatically replace the built-in `LoginInfo.vue` component at build time.
If no custom component is provided, the built-in login welcome content is used.

Authentication buttons and login behaviour remain managed by *datalab*.
The login controls are passed to the component as a `login` slot: place `<slot name="login" />` wherever they should appear (the built-in component puts them directly under the title).
If the slot is omitted, users will have no way to log in from this page.
The custom component should otherwise only provide branding, text, links, images, and styling for the login box.
To reuse content from [`CustomAbout.vue`](#custom-about-page-publiccustomcomponentscustomaboutvue), copy it into this component.
The deployment logo (`VUE_APP_LOGO_URL`) is already shown at the top of the box, so it does not need to be included.

For example:

```vue
<template>
  <h1>My lab datalab</h1>
  <p>Research data management for our group.</p>
  <slot name="login" />
</template>

<script>
export default {
  name: "CustomLoginInfo",
};
</script>
```

Login page colours and sizes can also be tuned from `public/custom/override.css` without providing a custom component:

```css
:root {
  --login-background: #f5f6f8; /* page background */
  --login-box-background: white;
  --login-box-color: #222;
  --login-max-width: 26rem; /* maximum width of the login box */
  --login-logo-max-width: 240px;
  --login-logo-max-height: 120px;
}
```

### Directory structure

A typical deployment customisation directory looks like:

```
public/custom/
├── override.css
├── fonts/
│   ├── MyFont-Regular.woff2
│   └── MyFont-Bold.woff2
├── logos/
│   └── mylogo.png
└── components/
    ├── CustomAbout.vue
    └── CustomLoginInfo.vue
```



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

::: pydatalab.config.ToolsSettings
    options:
      heading_level: 2
      show_root_heading: true
      show_source: false
