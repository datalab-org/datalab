# <div align="center">datalab</div>

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


<!-- datalab logo -->

This repository contains the code for a data management system that consists of
two main components:

- a Flask-based Python web server (`pydatalab`) that communicates with a MongoDB
  database backend and can perform simple analysis and ETL of particular data types,
- a Vue 3 web application for a GUI that can be used to record information on
  samples alongside raw data files and analysis documents.

The system was developed for and is currently deployed for the
[Grey Group](https://www.ch.cam.ac.uk/group/grey/)
in the Department of Chemistry at the University of Cambridge.


## Features

### Introductory video

https://github.com/the-grey-group/datalab/assets/7916000/0065cdd6-a5f0-4391-b192-0137fe208acc


### Server

- A REST API for accessing data and analysis related to chemical samples,
  inventory and their connections.
- OAuth2-based user authentication via GitHub or ORCID and simple user role
  management.
- Real-time data streaming and syncing with remote data sources (e.g., instrumentation, archives and file stores).

### UI

- A simple, intuitive UI for recording sample metadata and relationships with
  other samples (batches, offshoots), alongside synthesis parameters and raw data.
- Basic analysis and plotting of live and archived data attached to a sample, e.g.,
  characterisation via XRD or NMR, electrochemical cycling data and images (see "Data blocks" section for a complete list).
- Interactive network visualisation of the connections between samples and inventory.

## Development status

The software is still an alpha work-in-progress and the API, data models and UI may
change significantly between versions.


## Installation

Installation, usage and deployment instructions can be found in
[INSTALL.md](./INSTALL.md) and in the [online documentation](https://the-datalab.readthedocs.io).

## License

This software is released under the conditions of the MIT license.
Please see [LICENSE](./LICENSE) for the full text of the license.

## Contributions

This software was primarily developed by:

- [Joshua Bocarsly](https://jdbocarsly.github.io) ([Department of Chemistry, University of Houston](https://www.uh.edu/nsm/chemistry), previously [Department of Chemistry, University of Cambridge](https://www.ch.cam.ac.uk/))
- [Matthew Evans](https://ml-evs.science) ([MODL-IMCN,
  UCLouvain](https://uclouvain.be/en/research-institutes/imcn/modl) & [Matgenix](https://matgenix.com))

with contributions and testing performed by other members of the Grey Group.

<!-- uni logos -->

## Funding

This project has received funding from the European Union's Horizon 2020 research and innovation programme under grant agreement 957189 (DOI: [10.3030/957189](https://doi.org/10.3030/957189)), the [Battery Interface Genome - Materials Acceleration Platform (BIG-MAP)](https://www.big-map.eu), as an external stakeholder project.

<div align="center">
<img href="https://big-map.org" src="https://big-map.github.io/big-map-registry/static/img/big-map-white-transparent.png" width=100>
</div>

<!-- funding logos -->
