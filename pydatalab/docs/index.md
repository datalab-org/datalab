---
title: Documentation
hide:
  - toc
---

# *datalab* documentation

--8<-- "README.md:intro"

If you have never seen *datalab* before, the quickest introduction is to
[try the public demo instance](https://demo.datalab-org.io);
for background on the project itself, see [About *datalab*](about.md).

!!! important "Every *datalab* is different"
    *datalab* can be self-hosted and is extensible via plugins, so **no two deployments are alike**.
    These docs primarily describe the *upstream* project, rather than a specific *datalab* instance.

## Where to go next

<div class="grid cards home-cards" markdown>

-   :material-flask-outline:{ .lg .middle } __For users__

    ---

    Using a *datalab* instance: recording samples and cells,
    attaching data, and getting your data back out again.

    [:material-book-open-variant: &nbsp; User guide](https://guide.datalab-org.io)

    [:material-file-tree: &nbsp; Data models](schemas/items.md)

    [:material-cube-outline: &nbsp; Data blocks](blocks/reference/base.md)

    [:simple-python: &nbsp; Python API](https://github.com/datalab-org/datalab-api)

-   :material-code-braces:{ .lg .middle } __For developers__

    ---

    Extending *datalab* with your own blocks and plugins, or contributing to the
    core server and web app.

    [:material-console: &nbsp; Development setup](INSTALL.md)

    [:material-puzzle-outline: &nbsp; Writing plugins](plugins.md)

    [:material-api: &nbsp; Writing data blocks](blocks/index.md)

    [:material-map-marker-path: &nbsp; Roadmap](roadmap.md)

-   :material-server-network:{ .lg .middle } __For deployments__

    ---

    Deploying and administering an instance for your group or others.

    [:material-server: &nbsp; Deployment guide](deployment.md)

    [:material-cog-outline: &nbsp; Server configuration](config.md)

    [:simple-ansible: &nbsp; Ansible & Terraform Automations](https://github.com/datalab-org/datalab-ansible-terraform)

    [:material-history: &nbsp; Changelog](CHANGELOG.md)

</div>

## Getting help

- Join the [public *datalab* Slack workspace](https://join.slack.com/t/datalab-world/shared_invite/zt-2h58ev3pc-VV496~5je~QoT2TgFIwn4g) to ask questions and hear about releases.
- Report bugs and request features on [GitHub](https://github.com/datalab-org/datalab/issues).
- Managed deployments and consultancy are available from [*datalab industries ltd.*](https://datalab.industries) — [hello@datalab.industries](mailto:hello@datalab.industries).
