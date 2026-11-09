<div align="center"><img width="250" height="250" alt="logo" src="https://github.com/user-attachments/assets/b952e1f2-7ccb-4245-aaf1-1923a7c87bfd" /></div>


# <div align="center"><i>datalab</i></div>


<div align="center" style="padding-bottom: 5px">
<a href="https://demo.datalab-org.io"><img src="https://img.shields.io/badge/try_it_out!-public_demo_server-orange?logo=firefox"></a>
<a href="https://github.com/datalab-org/datalab#MIT-1-ov-file"><img src="https://img.shields.io/github/license/datalab-org/datalab?color=purple&logo=github"></a>
<a href="https://the-datalab.readthedocs.io/en/latest/?badge=latest"><img src="https://img.shields.io/readthedocs/the-datalab?logo=readthedocs"></a>
<a href="https://join.slack.com/t/datalab-world/shared_invite/zt-2h58ev3pc-VV496~5je~QoT2TgFIwn4g"><img src="https://img.shields.io/badge/Slack-chat_with_us-yellow?logo=slack"></a>
</div>

<!-- --8<-- [start:intro] -->
_datalab_ is a user-friendly, open-source platform that can capture all the experimental data and metadata produced in a scientific lab, targeted (broadly) at materials chemistry but with customisability and extensability in mind.
_datalab_ records data and metadata securely and makes it accessible and reusable by both humans and machines _via_ the web UI and API, respectively.
_datalab_ can be self-hosted and managed deployments are also available.
<!-- --8<-- [end:intro] -->

You can try the demo deployment at [demo.datalab-org.io](https://demo.datalab-org.io/) and read the online documentation at [docs.datalab-org.io](https://docs.datalab-org.io) with release notes and changelog available on [GitHub](https://github.com/datalab-org/datalab/releases/) and [online](https://docs.datalab-org.io/en/latest/CHANGELOG).

## Features

<!-- --8<-- [start:features] -->
* Capture and store sample and device metadata
* Connect and sync raw data directly and from laboratory instruments
* [Built-in support](https://docs.datalab-org.io/en/latest/blocks/) for multiple characterisation techniques (XRD, NMR, echem, TEM, TGA, Mass Spec, Raman and more).
* Capture scientific context: store the graph of relationships between research objects.
* [Python API](https://github.com/datalab-org/datalab-api) for programmatic access to your lab's data enabling custom analysis and automation.
* Join the [_datalab_ federation](https://github.com/datalab-org/datalab-federation): you can add your _datalab_ to the federation for additional shared features.
* [Plugin ecosystem](https://docs.datalab-org.io/en/latest/plugins) allowing for custom data blocks, [AI integration](https://github.com/datalab-org/yellowhammer) and other instance-specific code.
* [Deployment and infrastructure automation](https://github.com/datalab-industries/datalab-ansible-terraform) via Ansible playbooks.
<!-- --8<-- [end:features] -->

> [!NOTE]
> You may be looking for the identically named project [DataLab](https://datalab-platform.com) for signal processing, which also has plugins, clients and other similar concepts!

## Getting started

The full documentation lives at [docs.datalab-org.io](https://docs.datalab-org.io), split by audience:

- **[For users](https://guide.datalab-org.io/)** — using an instance that someone else runs: recording samples and cells, attaching data, and getting it back out again via the [Python API](https://github.com/datalab-org/datalab-api).
- **[For developers](https://docs.datalab-org.io/en/latest/INSTALL)** — running *datalab* locally, writing [plugins](https://docs.datalab-org.io/en/latest/plugins), and contributing to the core.
- **[For deployments](https://docs.datalab-org.io/en/latest/deployment)** — standing up and [configuring](https://docs.datalab-org.io/en/latest/config) an instance for your group.

Note that *datalab* is self-hosted and plugin-extensible, so no two instances are alike: the item types, data blocks and metadata fields available to you depend on how your instance has been configured and which plugins it has installed.

We can also provide paid managed deployments via [_datalab industries ltd._](https://datalab.industries): contact us at [hello@datalab.industries](mailto:hello@datalab.industries).

## License

This software is released under the conditions of the MIT license.
Please see [LICENSE](./LICENSE) for the full text of the license.

## Citation

Should you use _datalab_ in your research, please consider citing the following paper:

<!-- --8<-- [start:citation] -->
> Matthew L. Evans, Joshua D. Bocarsly, Benjamin Charmes, Ben E. Smith, Gian-Marco Rignanese, David Waroquiers, Clare P. Grey, **datalab: federated data management infrastructure for materials chemistry and beyond**, _Journal of Open Source Software_ **11** (126), 10652 (2026). DOI: [10.21105/joss.10652](https://doi.org/10.21105/joss.10652)
<!-- --8<-- [end:citation] -->

## Contact

We are available for consultations on setting up and managing *datalab* deployments, as well as collaborating on or sponsoring additions of new features and techniques. Please contact Josh or Matthew on their academic emails, or join the [public *datalab* Slack workspace](https://join.slack.com/t/datalab-world/shared_invite/zt-2h58ev3pc-VV496~5je~QoT2TgFIwn4g).

## Contributions

Bug reports, feature requests and pull requests are all welcome.
Please see [CONTRIBUTING.md](CONTRIBUTING.md) for how to get started, what we expect from a
contribution, and our policy on AI-assisted changes.

<!-- --8<-- [start:credits] -->
This software was conceived and developed by:

- [Prof Joshua Bocarsly](https://jdbocarsly.github.io) ([Department of Chemistry, University of Houston](https://www.uh.edu/nsm/chemistry), previously [Department of Chemistry, University of Cambridge](https://www.ch.cam.ac.uk/))
- [Dr Matthew Evans](https://ml-evs.science) ([Department of Chemistry, University of Cambridge](https://www.ch.cam.ac.uk/), previously [MODL-IMCN,
  UCLouvain](https://uclouvain.be/en/research-institutes/imcn/modl) & [Matgenix](https://matgenix.com))

with support from the group of [Professor Clare Grey](https://grey.group.ch.cam.ac.uk/group) (University of Cambridge), and major contributions from:

- [Benjamin Charmes](https://github.com/BenjaminCharmes)
- [Dr Ben Smith](https://github.com/be-smith/)
- [Dr Yue Wu](https://github.com/yue-here)

plus many contributions, feedback and testing performed by other members of the community, in particular, the groups of [Prof Matt Cliffe](https://cliffegroup.co.uk) (University of Cambridge) and [Dr Peter Kraus](https://www.tu.berlin/en/concat) (TUBerlin) and the company [Matgenix SRL](https://matgenix.com).

A full list of code contributions can be found on [GitHub](https://github.com/datalab-org/datalab/graphs/contributors).

## Funding

Contributions to _datalab_ have been supported by a mixture of academic funding and consultancy work through [_datalab industries ltd_](https://datalab.industries).

In particular, the developers thank:

- Initial proof-of-concept funding from the European Union's Horizon 2020 research and innovation programme under grant agreement 957189 (DOI: [10.3030/957189](https://doi.org/10.3030/957189)), the [Battery Interface Genome - Materials Acceleration Platform (BIG-MAP)](https://www.big-map.eu), as an external stakeholder project.
- The [Faraday Institution](https://www.faraday.ac.uk) CATMAT project (FIRG016) for support of Dr Joshua Bocarsly during initial development of *datalab*.
- The [Leverhulme Trust](https://leverhulme.ac.uk) and [Isaac Newton Trust](https://newtontrust.cam.ac.uk) for support provided by an early career fellowship for Dr Matthew Evans.
<!-- --8<-- [end:credits] -->
