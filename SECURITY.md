# Security Policy

*datalab* is typically used to store research data - much of it unpublished, some of it commercially or academically sensitive - on infrastructure operated by the research groups and consortia that use it. This document describes how to report a vulnerability, what the software defends against, and which parts of the problem are necessarily left to whoever deploys it.

## Reporting a vulnerability

**Please do not report security issues in public GitHub issues.**

Report privately through either channel:

- [GitHub private vulnerability reporting](https://github.com/datalab-org/datalab/security/advisories/new) (preferred)
- Email `dev@datalab-org.io`

Please include the affected version, a description of the issue, and ideally a proof of concept and an assessment of impact.

What to expect:

| Stage | Target |
| --- | --- |
| Acknowledgement of your report | 3 working days |
| Initial assessment and severity triage | 10 working days |
| Fix or documented mitigation for high-severity issues | 90 days from triage |

We will keep you updated as we work, credit you in the advisory unless you would
rather we didn't, and publish a GitHub Security Advisory when a fix is released.
If we conclude a report is not a vulnerability, we will explain why.

*datalab* is maintained by a small academic-focused team (with commercial support
through [datalab industries ltd.](https://datalab.industries)), not a dedicated security
organisation.

We will not pursue or support legal action against researchers who act in good
faith: testing only against instances they own or have written permission to test,
avoiding access to other people's data, avoiding degradation of live services, and
giving us reasonable time to respond before disclosing publicly.

**Do not test against instances you do not operate**, including the public demo — most deployments
hold real, unpublished research data belonging to third parties.

## Supported versions

Security fixes are issued for the **latest released minor version** only (currently the `v0.7.x` series).
*datalab* is pre-1.0 and under active development; operators are expected to track releases reasonably closely.

## Trust model

### What the software enforces

- **Authenticated access.** Users authenticate via OAuth (ORCID, GitHub), magic-link
  email, or API keys. Registration can be restricted by GitHub organisation
  membership or email domain, and accounts require admin activation by default.
- **Per-item and per-group permissions.** Every read and write is filtered by a
  permission query derived from the requesting user's identity, their group
  memberships, and any managed users. Items may inherit read access from collections
  they belong to; write access is never inherited.
- **Hashed credentials at rest.** API keys and item access tokens are stored as
  hashes, never in plaintext.
- **A write audit trail.** Item edits are snapshotted as versions, attributed to the
  user who made them.

### What it does not defend against

- **Instance administrators.** An admin can read every item in the deployment via
  super-user mode. This is intentional but it means *the operator of a shared or
  consortium instance can see all members' data*.
  Consortia should establish who holds admin, and satisfy themselves about the governance around it, as an organisational control.
  Improved logging of administrative reads is [planned](#planned-work).
- **Plugins.** Plugins are Python packages loaded into the server process. They have
  full access to the database, the filesystem, and the network — the same trust level
  as any other installed dependency. **Installing a plugin is a deployment decision
  with the same weight as a code change**, and should be reviewed as one. There is no
  sandbox, and adding one is [non-trivial](#planned-work).
- **Malicious authenticated users.** Users are treated as semi-trusted colleagues.
  Permissions constrain which data they reach, but a user who is authenticated and
  actively hostile has a large surface to work with — notably file uploads, which are
  parsed by a wide range of third-party scientific libraries which may be
  vulnerable to exploitation.
- **Infrastructure compromise.** Host, container runtime, database, and network
  security are the operator's responsibility.

## What the project does upstream

Practices in place in this repository today:

**Dependency management**
- Dependabot covers four ecosystems monthly: Python (`uv`), npm, GitHub Actions, and the Docker base images.
- Security advisories are provided by GitHub and Dependabot, and are triaged by the maintainers. Critical advisories are addressed in patch releases as soon as possible.
- A scheduled workflow refreshes `uv.lock` pins monthly, so transitive dependencies don't drift and quietly retain known-vulnerable versions.
- Server dependencies are fully pinned via `uv.lock`; CI and container builds install from the lockfile.
- Aside from internal Python packages, no dependency newer than 5 days old is used in production.
- JavaScript app dependencies are pinned to exact versions in `yarn.lock`; `yarn install --frozen-lockfile` is used in CI and container builds.

**Static analysis and CI**
- For server code, `ruff` runs with the [`flake8-bandit`](https://docs.astral.sh/ruff/rules/#flake8-bandit-s)
  (`S`) security ruleset enabled, alongside `mypy` type checking. Both are enforced
  in CI through pre-commit, not merely available locally.
- The full test suite runs against a matrix of supported Python versions on every
  pull request, with coverage reported.
- The webapp is built and linted with `eslint` and this build is tested in CI on every pull request.
- The web app is tested with a suite of Cypress end-to-end and component
  tests, run in the CI on every pull request.
- The web app build and the plugin-installation path are both exercised in CI.
-

**Application hardening**
- The Flask `SECRET_KEY` is checked for sufficient entropy at startup; the server
  refuses to run with a weak or absent key unless an explicit insecure-override
  environment variable is set.
- Cross-origin access is split by credential type: the public API is readable from
  any origin using an explicit `DATALAB-API-KEY` header, while cookie-authenticated
  sessions are restricted to configured first-party origins.
- Uploaded filenames are sanitised before being written to disk.
- User-supplied SVG and Markdown are sanitised with DOMPurify before rendering.

**Release integrity**
- PyPI releases use [Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
  via OIDC, so no long-lived publishing token exists to be stolen.
- Releases are built from tagged commits in GitHub Actions environments requiring
  approval.

## Operator responsibilities

*datalab* is self-hostable, and a correctly written application on a badly configured
host is not secure. The following are the deploying institution's responsibility:

- **Transport security.** Terminate TLS at a reverse proxy and set
  `BEHIND_REVERSE_PROXY`. Never expose the API directly over plain HTTP.
- **Database access.** MongoDB should be reachable only from the API container.
  Enable authentication on the database if it is reachable from anywhere else.
- **Origin configuration.** Set `APP_URL` to the web app's URL so that
  cookie-authenticated requests are restricted to it.
- **Secrets.** Supply `PYDATALAB_SECRET_KEY` and any OAuth secrets from the
  environment or a secrets manager, never from a file in version control. Rotating
  the secret key invalidates all sessions.
- **Storage encryption.** Enable full-disk encryption on the host volume, and
  encrypt backup artifacts — especially any shipped off-host. Note the limits of
  this: it protects against a stolen disk or a leaked snapshot, and not at all
  against compromise of a running server, since the database decrypts transparently
  for anyone who can connect.
- **Backups.** Configure and, importantly, **periodically test restoring** them.
  An untested backup is not a backup.
- **Remote filesystems.** Scope any configured remote filesystem to the narrowest
  possible directory, using a dedicated account with read-only access.
- **Plugins.** Review and pin them; treat additions as deployment changes.
- **Updates.** Track releases and subscribe to this repository's security advisories.

There are a series of Ansible roles made available by datalab industries ltd. in
[`datalab-ansible-terraform`](https://github.com/datalab-industries/datalab-ansible-terraform) that cover several of these cases automatically.
For example, certificate provisioning, backup scheduling and retention, monitoring and log ingestion are handled by the
playbooks.
See the deployment repository's own `SECURITY.md` for the infrastructure-side half of this policy.

## Planned work

Improvements we intend to make. They are listed here so operators can see what is
coming and what is not yet true; **several are only meaningful in combination with a
particular deployment**, and none should be assumed present in a running instance.

- **A separate audit log stream.** Security-relevant events (administrative reads,
  authentication, permission elevation) currently go to the general application log,
  which rotates with everything else. Emitting them on a dedicated logger would let
  operators retain them for longer and ship them to separate storage. *The retention
  and destination remain a deployment choice — the software can only make the events
  cleanly separable.*
- **Explicit logging of administrative reads.** So that use of super-user mode is
  attributable, which matters most for consortium instances where admin and data
  owner are different institutions.
- **Plugin provenance in the API.** Reporting the providing package, version, and
  source for each block through `/info`, so that members of a shared instance can
  inspect what code is running without server access.
- **Process isolation for block execution.** Running block parsing in a worker with
  no database credentials and no network egress. This is a substantial change; the
  asynchronous block infrastructure is the groundwork for it.
- **Explicit session cookie flags.** Setting `SameSite`, `Secure`, and `HttpOnly`
  deliberately rather than relying on framework defaults.
- **Additional static analysis**, such as CodeQL, to complement the existing `ruff`
  security ruleset.

If any of these are blocking an adoption decision, please open an issue or get in
touch; knowing which matter to real deployments helps us prioritise future development.
