<h1 align="center">
datalabvue
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
  characterisation via XRD or NMR, electrochemical cycling data and images -- see Blocks for a complete list.
- Interactive network visualisation of the connections between samples and inventory.

## Development status

The software is still an alpha work-in-progress and the API, data models and UI may
change significantly between versions.


## Installation

Installation, usage and deployment instructions can be found in
[INSTALL.md](./INSTALL.md) and in the [online documentation](https://readthedocs.com/datalab).

## License

This software is released under the conditions of the MIT license.
Please see [LICENSE](./LICENSE) for the full text of the license.

## Contributions

This software was primarily developed by:

- [Joshua Bocarsly](https://engineering.ucsb.edu/~jdbocarsly/) (Department of Chemistry, University of Cambridge)
- [Matthew Evans](https://ml-evs.science) ([MODL-IMCN,
  UCLouvain](https://uclouvain.be/en/research-institutes/imcn/modl) & [Matgenix](https://matgenix.com))

with contributions and testing performed by other members of the Grey Group.

<!-- uni logos -->

## Funding

This project has received funding from the European Union's Horizon 2020 research and innovation programme under grant agreement 957189 (DOI: [10.3030/957189](https://doi.org/10.3030/957189)), the [Battery Interface Genome - Materials Acceleration Platform (BIG-MAP)](https://www.big-map.eu), as an external stakeholder project.

<!-- funding logos -->
