# Contributing to *datalab*

*datalab* is developed in the open and we welcome bug reports, feature requests, documentation fixes and code from anyone using it.

*datalab* runs in production in research groups around the world, and each deployment is self-hosted and extended with its own plugins.
That shapes what we look for in a contribution more than anything else: changes should be incremental, backwards-compatible, and safe to pick up mid-term without anyone losing data.

## Code of conduct

We expect all contributors to follow the [code of conduct](CODE_OF_CONDUCT.md) in all interactions with the project.

## Before you start

**Please search for and open issues before writing code**, whether you are fixing a bug or adding a feature.
It is the cheapest way to find out that someone is already working on something, that the change belongs in a plugin rather than the core, or that it needs a different shape to fit the deployments we support.
There may also be ongoing larger PRs that are close to merging that we would suggest you base your changes upon, rather than introducing conflicts or delays in merging.

If the change is small and/or obvious, e.g., a typo or a broken link, then please go straight to a pull request.

Places to look first:

- [Open issues](https://github.com/datalab-org/datalab/issues), particularly those labelled [suggestions](https://github.com/datalab-org/datalab/issues?q=sort%3Aupdated-desc%20is%3Aissue%20is%3Aopen%20label%3Asuggestions), [EPIC](https://github.com/datalab-org/datalab/issues?q=sort%3Aupdated-desc+state%3Aopen+label%3A%22EPIC%22+) and [plugin-request](https://github.com/datalab-org/datalab/issues?q=sort%3Aupdated-desc+state%3Aopen+label%3A%22plugin-request%22+).
- The [roadmap](https://docs.datalab-org.io/en/latest/roadmap/), which collects the larger planned pieces of work. If your use case depends on something there, say so on the relevant issue to helps us prioritise future developments.

## What we expect from a contribution

We have some instructions for AI agents that may also be useful for humans at
[`AGENTS.md`](https://github.com/datalab-org/datalab/blob/main/AGENTS.md) at the repository root.

- **Most new domain code belongs in a plugin**, not in the core `apps/` directory.
  See the [plugin docs](https://docs.datalab-org.io/en/latest/plugins/) and the [plugin template](https://github.com/datalab-org/datalab-app-plugin-template).
- **Avoid database migrations.** Prefer new optional fields with `None` defaults, so that documents in existing deployments stay valid.
- **Extend tests rather than editing existing assertions.** If an existing expected value genuinely has to change, change it deliberately and explain why in the pull request.
- **Stay backwards-compatible.** Where a breaking change is unavoidable, provide a migration path and flag it clearly.
- **Document what you add.** Update the README, the installation guide or the relevant page under `pydatalab/docs/` rather than relying on code comments alone.

## AI-assisted contributions

Whilst we are not opposed to contributions written with the help of AI tools, we assert that **every AI-assisted commit must be reviewed by a human before it is submitted**.

Concretely, we ask that you:

- Do not list an AI tool as an author or co-author. The person who reviewed the change is the author, and takes responsibility for it.
- Read every line you submit. If you cannot explain why a change is correct, it is not ready.
- Keep AI-assisted pull requests small. Large generated diffs are difficult to review and are likely to be closed with a request to break them up.
- Configure your tooling to read our [`AGENTS.md`](https://github.com/datalab-org/datalab/blob/main/AGENTS.md) file and follow the instructions there.
  (For Claude code, this may mean symlinking your `CLAUDE.md` to `AGENTS.md` or otherwise referring to it via `@AGENTS.md` in your prompt.)

Agents working in this repository are instructed (via [`AGENTS.md`](https://github.com/datalab-org/datalab/blob/main/AGENTS.md)) to leave a comment at the top of each file they edit noting that it requires human review.
Remove those comments once you have done that review.

## Development setup

The [installation guide](https://docs.datalab-org.io/en/latest/INSTALL/) covers running the server and web app locally. In short:

```bash
# Python server
cd pydatalab && uv sync --all-extras --dev --locked && uv run pytest

# Web app
cd webapp && yarn install && yarn test:e2e
```

Please install the pre-commit hooks before your first commit, as CI runs the same checks:

```bash
pre-commit install
pre-commit run --all-files
```

## Getting help

- Ask in the [public *datalab* Slack workspace](https://join.slack.com/t/datalab-world/shared_invite/zt-2h58ev3pc-VV496~5je~QoT2TgFIwn4g).
- Open a [GitHub issue](https://github.com/datalab-org/datalab/issues) for bugs and feature requests.
