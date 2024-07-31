# <div align="center"><i>datalab</i></div>

<div align="center" style="padding-bottom: 5px">
<a href="https://demo.datalab-org.io"><img src="https://img.shields.io/badge/try_it_out!-public_demo_server-orange?logo=firefox"></a>
</div>

<div align="center">
<a href="https://github.com/datalab-org/datalab/releases"><img src="https://badgen.net/github/release/datalab-org/datalab?icon=github&color=blue"></a>
<a href="https://github.com/datalab-org/datalab#MIT-1-ov-file"><img src="https://badgen.net/github/license/datalab-org/datalab?icon=license&color=purple"></a>
</div>

<div align="center">
<a href="https://github.com/datalab-org/datalab/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/datalab-org/datalab/ci.yml?logo=github"></a>
<a href="https://cloud.cypress.io/projects/4kqx5i/runs"><img src="https://img.shields.io/endpoint?url=https://cloud.cypress.io/badge/simple/4kqx5i/main&style=flat&logo=cypress"></a>
<a href="https://the-datalab.readthedocs.io/en/latest/?badge=latest"><img src="https://img.shields.io/readthedocs/the-datalab?logo=readthedocs"></a>
</div>

<div align="center">
<a href="https://github.com/datalab-org/datalab-ansible-terraform">
  <img alt="Static Badge" src="https://img.shields.io/badge/Ansible-playbook-white?logo=ansible">
</a>
<a href="https://pypi.org/project/datalab-api">
  <img alt="PyPI - Version" src="https://img.shields.io/pypi/v/datalab-api?logo=pypi&label=Python%20API">
</a>
</div>

<div align="center">
<a href="https://join.slack.com/t/datalab-world/shared_invite/zt-2h58ev3pc-VV496~5je~QoT2TgFIwn4g"><img src="https://img.shields.io/badge/Slack-chat_with_us-yellow?logo=slack"></a>
</div>

This repository contains the code for the *datalab* data management system, targeted (broadly) at materials chemistry labs but with customisability and extensability in mind.

The main aim of *datalab* is to provide a platform for capturing the significant amounts of long-tail experimental data and metadata produced in a typical lab, and enable storage, filtering and future data re-use by humans and machines.
The platform provides researchers with a way to record sample- and cell-specific metadata, attach and sync raw data from instruments, and perform analysis and visualisation of many characterisation techniques in the browser (XRD, NMR, electrochemical cycling, TEM, TGA, Mass Spec, Raman).
Importantly, *datalab* stores a network of interconnected research objects in the lab, such that individual pieces of data are stored with the context needed to make them scientifically useful.

The system was originally developed in and is currently deployed for the
[Grey Group](https://www.ch.cam.ac.uk/group/grey/)
in the Department of Chemistry at the University of Cambridge.


<div align="center">
<video width="400" controls src="https://github.com/datalab-org/datalab/assets/7916000/0065cdd6-a5f0-4391-b192-0137fe208acc">
</video>
</div>

## Features

*datalab* consists of two main components:

- a Flask-based Python web server (`pydatalab`) that communicates with a MongoDB
  database backend and can perform simple analysis and ETL of particular data types,
- a Vue 3 web application for a GUI that can be used to record information on
  samples alongside raw data files and analysis documents.


### Server

- A REST API for accessing data and analysis related to chemical samples,
  inventory and their connections, with ergonomic access provided via the
  [*datalab* Python API](https://github.com/datalab-org/datalab-api).
- OAuth2-based user authentication via GitHub or ORCID and simple user role
  management.
- Real-time data streaming and syncing with remote data sources (e.g., instrumentation, archives and file stores).

### UI

- A simple, intuitive UI for recording sample-based metadata and relationships with
  other samples (batches, derivatives, _etc._), alongside synthesis parameters and raw data.
- Basic analysis and plotting of live and archived data attached to a sample, _e.g._,
  characterisation via XRD or NMR, electrochemical cycling data and images (see "Data blocks" section for a complete list).
- Interactive network visualisation of the connections between samples and inventory.

## Development status

*datalab* remains under active development, and the API, data models and UI may change significantly between versions without prior notice.
Where possible, breaking changes will be listed in the release notes for every pre-v1 release.

## Installation

Installation, usage and deployment instructions can be found in
[INSTALL.md](./INSTALL.md) and in the [online documentation](https://the-datalab.readthedocs.io).

## License

This software is released under the conditions of the MIT license.
Please see [LICENSE](./LICENSE) for the full text of the license.

## Contributions

This software was conceived and developed by:

- [Prof Joshua Bocarsly](https://jdbocarsly.github.io) ([Department of Chemistry, University of Houston](https://www.uh.edu/nsm/chemistry), previously [Department of Chemistry, University of Cambridge](https://www.ch.cam.ac.uk/))
- [Dr Matthew Evans](https://ml-evs.science) ([MODL-IMCN,
  UCLouvain](https://uclouvain.be/en/research-institutes/imcn/modl) & [Matgenix](https://matgenix.com))

with contributions and testing performed by other members of the Grey Group.

A full list of code contributions can be found on [GitHub](https://github.com/datalab-org/datalab/graphs/contributors).

## Contact

We are available for consultations on setting up and managing *datalab* deployments, as well as collaborating on or sponsoring additions of new features and techniques.
Please contact Josh or Matthew on their academic emails, or join the [public *datalab* Slack workspace](https://join.slack.com/t/datalab-world/shared_invite/zt-2h58ev3pc-VV496~5je~QoT2TgFIwn4g).

## Funding

This project has received funding from the European Union's Horizon 2020 research and innovation programme under grant agreement 957189 (DOI: [10.3030/957189](https://doi.org/10.3030/957189)), the [Battery Interface Genome - Materials Acceleration Platform (BIG-MAP)](https://www.big-map.eu), as an external stakeholder project.

<div align="center">
<img href="https://big-map.org" src="https://big-map.github.io/big-map-registry/static/img/big-map-white-transparent.png" width=100>
</div>
