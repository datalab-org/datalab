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

_datalab_ is a user-friendly, open-source platform that can capture all the experimental data and metadata produced in a scientific lab, targeted (broadly) at materials chemistry but with customisability and extensability in mind. _datalab_ stores data safely and makes it accessible and reusable by both humans and machines _via_ webUI and python API. _datalab_ can be run locally or in the cloud; it can be self-hosted and managed deployments are also available. Try the working demo deployment [here](https://demo.datalab-org.io/).

Features:

* Capture and store detailed sample data and metadata
* Connect and sync data directly from laboratory instruments
* Built-in support for multiple characterisation techniques (XRD, NMR, echem, TEM, TGA, Mass Spec, Raman; more under active development)
* Capture scientific context: store the graph of relationships between research objects
* [Python API](https://github.com/datalab-org/datalab-api) - Programmatic access for custom analysis and automation
* [_datalab_ federation](https://github.com/datalab-org/datalab-federation) - you can add your _datalab_ to the federation for additional shared features

> [!NOTE]
> You may be looking for the identically named project [DataLab](https://datalab-platform.com) for signal processing, which also has plugins, clients and other similar concepts!

## Getting started
To set up your own _datalab_ instance, follow the installation and deployment instructions in
[INSTALL.md](./INSTALL.md) and the [online documentation](https://the-datalab.readthedocs.io).

We also provide paid managed deployments: contact us at [hello@datalab.industries](mailto:hello@datalab.industries)

## Design Philosophy
The _datalab_ architecture is shown below:

<center>

```mermaid
graph TD
classDef actor fill:#0066CC,fill-opacity:0.3,stroke:#333,stroke-width:2px,color:#000;
classDef clientInterface fill:#00AA44,fill-opacity:0.3,stroke:#333,stroke-width:2px,color:#000;
classDef coreComponent fill:#FF6600,fill-opacity:0.3,stroke:#333,stroke-width:2px,color:#000;
classDef umbrellaLabel fill:#666666,fill-opacity:0.3,stroke:#666,stroke-width:1px,color:#000,rx:5,ry:5,text-align:center;
classDef subgraphStyle fill:#f9f9f9,fill-opacity:0.1,stroke:#ccc,stroke-width:1px;

    subgraph ExternalActors [External actors]
        direction TB
        User[User]
        Machine[Machine]
    end
    class User,Machine actor;
    class ExternalActors subgraphStyle;

    UmbrellaDesc["Raw instrument data,<br>annotations, connections"]
    class UmbrellaDesc umbrellaLabel;

    subgraph ClientInterfaces [Client interfaces]
        direction TB
        BrowserApp[_datalab_<br>Browser app]
        PythonAPI[_datalab_<br>Python API]
    end
    class BrowserApp,PythonAPI clientInterface;
    class ClientInterfaces subgraphStyle;

    subgraph Backend
        direction TB
        RESTAPI[_datalab_<br>REST API]
        MongoDB[MongoDB Database]
        DataLake[Data Lake]
    end
    class RESTAPI,MongoDB,DataLake coreComponent;
    class Backend subgraphStyle;

    User      <-- "User data I/O" --> UmbrellaDesc;
    Machine   <-- "Machine data I/O" --> UmbrellaDesc;

    UmbrellaDesc <-- "_via_ GUI" --> BrowserApp;
    UmbrellaDesc <-- "_via_ scripts" --> PythonAPI;

    BrowserApp  <-- "HTTP (Data exchange)" --> RESTAPI;
    PythonAPI   <-- "API calls (Data exchange)" --> RESTAPI;

    RESTAPI <-- "Annotations, connections" --> MongoDB;
    RESTAPI <-- "Raw and structured characterisation data" --> DataLake;

    linkStyle 0 stroke:#666,stroke-width:3px
    linkStyle 1 stroke:#666,stroke-width:3px
    linkStyle 2 stroke:#666,stroke-width:3px
    linkStyle 3 stroke:#666,stroke-width:3px
    linkStyle 4 stroke:#666,stroke-width:3px
    linkStyle 5 stroke:#666,stroke-width:3px
    linkStyle 6 stroke:#666,stroke-width:3px
    linkStyle 7 stroke:#666,stroke-width:3px

    click PythonAPI "https://github.com/datalab-org/datalab-api" "datalab Python API on GitHub" _blank
    click BrowserApp "https://github.com/datalab-org/datalab/tree/main/webapp" "datalab Browser App on GitHub" _blank
    click RESTAPI "https://github.com/datalab-org/datalab/tree/main/pydatalab" "pydatalab REST API on GitHub" _blank
```

</center>

The main aim of *datalab* is to provide a platform for capturing the significant amounts of long-tail experimental data and metadata produced in a typical lab, and enable storage, filtering and future data re-use by humans and machines. *datalab* is targeted (broadly) at materials chemistry labs but with customisability and extensability in mind.

The platform provides researchers with a way to record sample- and cell-specific metadata, attach and sync raw data from instruments, and perform analysis and visualisation of many characterisation techniques in the browser (XRD, NMR, electrochemical cycling, TEM, TGA, Mass Spec, Raman).

Importantly, *datalab* stores a network of interconnected research objects in the lab, such that individual pieces of data are stored with the context needed to make them scientifically useful.

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

We are available for consultations on setting up and managing *datalab* deployments, as well as collaborating on or sponsoring additions of new features and techniques. Please contact Josh or Matthew on their academic emails, or join the [public *datalab* Slack workspace](https://join.slack.com/t/datalab-world/shared_invite/zt-2h58ev3pc-VV496~5je~QoT2TgFIwn4g).

## Funding

This project has received funding from the European Union's Horizon 2020 research and innovation programme under grant agreement 957189 (DOI: [10.3030/957189](https://doi.org/10.3030/957189)), the [Battery Interface Genome - Materials Acceleration Platform (BIG-MAP)](https://www.big-map.eu), as an external stakeholder project.

<div align="center">
<img href="https://big-map.org" src="https://big-map.github.io/big-map-registry/static/img/big-map-white-transparent.png" width=100>
</div>
