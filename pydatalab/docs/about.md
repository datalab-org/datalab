---
title: About datalab
---

# About *datalab*

--8<-- "README.md:intro"

The main aim of *datalab* is to capture the significant amounts of long-tail experimental
data and metadata produced in a typical lab, and to enable storage, filtering and future
data re-use by both humans and machines.

## Features

--8<-- "README.md:features"

## Design philosophy and architecture

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

## Citation

Should you use *datalab* in your research, please consider citing the following paper:

--8<-- "README.md:citation"

## Contributions

--8<-- "README.md:credits"

## License

*datalab* is released under the terms of the MIT license; see [LICENSE](LICENSE) for the
full text.
