# <div align="center"><i>datalab</i></div>

<div align="center">
<a href="https://github.com/the-grey-group/datalab/actions/workflows/ci.yml">
<img src="https://img.shields.io/github/actions/workflow/status/the-grey-group/datalab/ci.yml?logo=github">
</a>
<a href="https://cloud.cypress.io/projects/4kqx5i/runs">
<img src="https://img.shields.io/endpoint?url=https://cloud.cypress.io/badge/simple/4kqx5i/main&style=flat&logo=cypress">
</a>
<a href="https://the-datalab.readthedocs.io/en/latest/?badge=latest">
<img
src="https://img.shields.io/readthedocs/the-datalab?logo=readthedocs&color=blueviolet">
</a>
</div>

</h1>

> 📢 If you are interested in joining the *datalab* mailing list and helping decide its future, please fill out [the survey](https://forms.gle/etq4pcsQJ3omLBmj6).

> ℹ️ We have created a public deployment of *datalab* for potential users to test. Please register via the magic-link email sign in at [public.datalab.odbx.science](https://public.datalab.odbx.science). Any data stored here will not be visible to others except the admins of the deployment, where it will only be used for debugging purposes. We provide no assurances for availability or data backups on this deployment, so please do not use this for production work.

<!-- datalab logo -->

This repository contains the code for the *datalab* data management system, targeted (broadly) at materials chemistry labs but with customisability and extensability in mind.

The main aim of *datalab* is to provide a platform for capturing the significant amounts of long-tail experimental data and metadata produced in a typical lab, and enable storage, filtering and future data re-use by humans and machines.
The platform provides researchers with a way to record sample- and cell-specific metadata, attach and sync raw data from instruments, and perform analysis and visualisation of many characterisation techniques in the browser (XRD, NMR, electrochemical cycling, TEM, TGA, Mass Spec, Raman).
Importantly, *datalab* stores a network of interconnected research objects in the lab, such that individual pieces of data are stored with the context needed to make them scientifically useful.

*datalab* consists of two main components:

- a Flask-based Python web server (`pydatalab`) that communicates with a MongoDB
  database backend and can perform simple analysis and ETL of particular data types,
- a Vue 3 web application for a GUI that can be used to record information on
  samples alongside raw data files and analysis documents.

The system was originally developed in and is currently deployed for the
[Grey Group](https://www.ch.cam.ac.uk/group/grey/)
in the Department of Chemistry at the University of Cambridge.


## Features

### Introductory video

<div align="center">
<video controls src="https://github.com/the-grey-group/datalab/assets/7916000/0065cdd6-a5f0-4391-b192-0137fe208acc">
</video>
</div>

### Server

- A REST API for accessing data and analysis related to chemical samples,
  inventory and their connections.
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

A full list of code contributions can be found on [GitHub](https://github.com/the-grey-group/datalab/graphs/contributors).

## Contact

We are available for consultations on setting up and managing *datalab* deployments, as well as collaborating on or sponsoring additions of new features and techniques.
Please contact Josh or Matthew on their academic emails, or use the catch-all address datalab@odbx.science if you are interested.

## Funding

This project has received funding from the European Union's Horizon 2020 research and innovation programme under grant agreement 957189 (DOI: [10.3030/957189](https://doi.org/10.3030/957189)), the [Battery Interface Genome - Materials Acceleration Platform (BIG-MAP)](https://www.big-map.eu), as an external stakeholder project.

<div align="center">
<img href="https://big-map.org" src="https://big-map.github.io/big-map-registry/static/img/big-map-white-transparent.png" width=100>
</div>
