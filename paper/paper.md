---
title: '*datalab*: federated data management infrastructure for materials chemistry and beyond'
authors:
  - name: Matthew L. Evans
    orcid: 0000-0002-1182-9098
    affiliation: "1, 2, 3, 4"
    equal-contrib: true
  - name: Joshua D. Bocarsly
    orcid: 0000-0002-7523-152X
    affiliation: "5, 6"
    equal-contrib: true
  - name: Benjamin Charmes
    orcid: 0009-0007-9474-8632
    affiliation: "1, 4"
  - name: Ben E. Smith
    orcid: 0000-0001-9673-2449
    affiliation: "4"
  - name: Gian-Marco Rignanese
    affiliation: "2, 7"
    orcid: 0000-0002-1422-1205
  - name: David Waroquiers
    affiliation: "3"
    orcid: 0000-0001-8943-9762
  - name: Clare P. Grey
    orcid: 0000-0001-5572-192X
    affiliation: "1"
affiliations:
 - name: Yusuf Hamied Department of Chemistry, University of Cambridge, Cambridgeshire, United Kingdom
   index: 1
 - name: Institute of Condensed Matter and Nanosciences, Université catholique de Louvain, Chemin des Étoiles 8, Louvain-la-Neuve 1348, Belgium
   index: 2
 - name: Matgenix SRL, Rue Armand Bury 185, 6534 Gozée, Belgium
   index: 3
 - name: datalab industries ltd., King's Lynn, Norfolk, United Kingdom
   index: 4
 - name: Department of Chemistry, University of Houston, Houston, TX, USA
   index: 5
 - name: Texas Center for Superconductivity, University of Houston, Houston, TX, USA
   index: 6
 - name: WEL Research Institute, Avenue Pasteur, 6, 1300 Wavre, Belgium
   index: 7

date: March 2026
bibliography: paper.bib
rsecon26: accepted
---

# Summary

*datalab* is an open source laboratory data management platform for chemical and material sciences, consisting of a Python web server, user-friendly Vue.js web app, and an associated ecosystem of plugins and tools.
It is designed to be deployed at the level of a research group or consortium, providing functionality to track samples and their connections through the entire research lifecycle. In doing so, *datalab* seeks to enable FAIR (Findable, Accessible, Interoperable and Reusable) [@Wilkinson2016; @Scheffler2022a] data workflows while simultaneously saving researchers time and effort in managing and analyzing experiments.

# Statement of need

As the quantity and diversity of scientific data collected in research laboratories grows, data management becomes an increasingly important challenge.
Research organizations, funders, and publishers have recently emphasized the importance of FAIR data. Despite this recognized need, the majority of lab data is not managed in such a way that it could be accessed and reused, even within individual research groups.
For example, a recent survey by the UK’s Physical Sciences Data Infrastructure (PSDI) found that fewer than 20% of respondents digitally managed all of their laboratory data and experiments [@Kanza2023].
One reason for this poor adoption rate is the challenges involved in practical data management for experimental labs: diverse data types in a variety of formats, complex interconnected experiments, and constantly evolving objectives.
Therefore, data management platforms that can enable user-friendly recording of diverse data and metadata have the potential to enable greater reproducibility, accelerated data analysis, and improved data sharing.
The recent growth in data-driven research and artificial intelligence (AI) for chemistry and materials underscores the importance of effective research data management [@Mroz2025].

# State of the field

Currently, there are several open-source electronic lab notebooks (ELNs) or Laboratory Information Management Systems (LIMSs) aimed at performing FAIR research data management in the experimental chemical and materials sciences. Each package draws a different boundary around which types of data and aspects of the data lifecycle they intend to cover. Importantly, these frameworks are often relied on not just for data recording, but also robust backed-up file storage, syncing from remote scientific instruments, data sharing and collaboration, and data analysis and visualization [@Higgins2022].
Exemplary open source frameworks include: [NOMAD](https://nomad-lab.eu/nomad-lab) [@Scheidgen2023; @Ghiringhelli2023], [openBIS](https://openbis.ch) [@Barillari2016; @Lam2025], [eLabFTW](https://www.elabftw.net), [Chemmotion](https://chemotion.net) [@Tremouilhac2017a; @Herrmann2025], [Kadi4Mat](https://kadi.iam.kit.edu) [@Brandt2021; @Schlabach2024] and [SampleDB](https://scientific-it-systems.iffgit.fz-juelich.de/SampleDB) [@Rhiem2021].

One dividing line between the various existing approaches is the balance between extensibility and ease-of-use, with some platforms being highly customizable at the expense of requiring substantial technical expertise. Another differentiator is in the manner in which raw data makes its way into the platform, i.e., whether the user must pre-process data into a generic format or if the platform can directly ingest data from instruments.

# Software design

*datalab* consists of a server (using [Flask](https://flask.palletsproject.com)), a database ([MongoDB](https://mongodb.com)), and a web frontend (written in [Vue.js](https://vuejs.org)), alongside a growing ecosystem of plugins and tools.
This stack is designed to be deployed and configured for a single research group or research consortium, allowing users to record all the data involved in their research projects.

The core data model is inspired by how researchers traditionally record data in physical lab notebooks. Each sample or device (generically, `Item`) studied in a lab is stored as a document in the database. Unique identifying information for each item is recorded along with information such as its chemical formula, synthesis procedure, chemical hazard statements, qualitative notes, etc., along with data files and visualizations from any measurements that were performed on that sample. Similar interfaces are also provided for managing a chemical inventory, and lab equipment.

Data models for `Item`s are described with [Pydantic](https://pydantic.dev) models and are kept relatively lightweight: enforcing critical information (e.g., a unique id and date), specifying useful optional fields (e.g., chemical formula), and always including arbitrary free-text fields to allow for the flexibility required by the often-unpredictable nature of laboratory research. If needed, the base schemas can also be extended to specify additional fields for specialized `Item` types studied in a given lab (e.g., battery cells). The user is provided with a simple web interface to input, edit, and view data, including interactive views of their measurement data. A Python client library, [datalab-org/datalab-api](https://github.com/datalab-org/datalab-api) is also available to streamline access and perform more complicated tasks, such as aggregated searches, or downstream tasks like syncing with a chemical inventory system ([datalab-industries/datalab-cheminventory-plugin](https://github.com/datalab-industries/datalab-cheminventory-plugin)) or other remote filesystem/API ([datalab-industries/datalab-beholder-plugin](https://github.com/datalab-industries/datalab-beholder-plugin)).

In addition to data and metadata, *datalab* also emphasizes recording connections between items, such as linking samples to the starting materials (or other samples) that were used in their synthesis, or linking battery test cells to the electrode materials that were used in the cell construction. This creates an evolving graph of connected research items that is stored in the database and displayed in the GUI, allowing researchers to explore measurements from associated items.

The measurement data, which are quite variable and diverse in typical experimental labs, are handled via modular "data blocks" that consist of raw data parsers, validators and visualizers. Data blocks can be written as applications in Python, generally using [Bokeh](https://bokeh.org) for interactive visualizations. A core set of commonly used blocks is included in the core of *datalab*, while others can be added using a plugin system.

These data blocks vary in complexity, from simple CSV parsing and visualization, up to two-way reactive components that can perform automated analysis (normalization, baseline corrections), capture additional out-of-band metadata from the user (e.g., the wavelength used in an X-ray diffraction experiment, where not provided in the file), and index particular properties or metadata in the database for future search (e.g., peak positions or $d$-spacings from an X-ray diffraction experiment).
Data blocks can be rendered either synchronously or asynchronously, via simple scheduled background tasks, depending on the application. Table 1 provides a non-exhaustive summary of the support for different characterization techniques and file types in the current version of the *datalab* core.

Much of this support is provided by other third-party libraries (many of which the *datalab* community helps to maintain), for example, `galvani` [@Kerr2017] for electrochemical data and `nmrglue` [@Helmus2013] for NMR data, which are wrapped in *datalab* data blocks to provide a user-friendly experience and indexing of metadata for use in the rest of the system.

```{=latex}
\begin{table}[ht]
\caption{Non-exhaustive summary of supported characterization techniques and file formats. Some are included in the \emph{datalab} core, while others are open-source plugins built using the extensible plugin system (denoted by $\star$).}
\label{tbl:formats}
\small
\begin{tabular}{|l|l|}
\hline
\textbf{Technique} & \textbf{File formats \& vendors} \\
\hline
X-ray diffraction (XRD) & \begin{tabular}[t]{@{}l@{}} - Plain text semi-standardized \texttt{.xy}, \texttt{.xye}, \texttt{.dat} \\ - Bruker \texttt{.raw} \\ - Panalytical XRDML \\ - Rigaku \texttt{.rasx} \end{tabular} \\
\hline
Nuclear magnetic resonance (NMR) & \begin{tabular}[t]{@{}l@{}} - JCAMP-DX \\ - Bruker project folders (zipped) \\ - JEOL \texttt{.jdf} \end{tabular} \\
\hline
Electrochemical cycling & \begin{tabular}[t]{@{}l@{}} - Battery Data Format \texttt{.bdf} \\ - BioLogic \texttt{.mpr} \\ - Arbin \texttt{.res} \\ - Neware \texttt{.nda}, \texttt{.ndax} \\ - Plain text and Excel exports from various \\ \quad vendor software packages (e.g., Lanhe/Landt, \\ \quad Ivium, Arbin) \end{tabular} \\
\hline
Electrochemical impedance spectroscopy (EIS) & \begin{tabular}[t]{@{}l@{}} - BioLogic \texttt{.mpr} \\ - Ivium-exported \texttt{.txt} \end{tabular} \\
\hline
Ultraviolet-visible (UV-Vis) spectroscopy & \begin{tabular}[t]{@{}l@{}} - Plain text and Excel exports \\ \quad from various vendor software packages \end{tabular} \\
\hline
Raman spectroscopy and microscopy & - Renishaw \texttt{.wdf} \\
\hline
Fourier-transform infrared (FTIR) spectroscopy & - Agilent \texttt{.asc} \\
\hline
Mass spectrometry (MS) & - Mettler-Toledo \texttt{.asc} \\
\hline
${\star}$ Differential scanning calorimetry (DSC) & - TA Instruments text exports \\
\hline
${\star}$ Online mass spectrometry (OMS) & - Pfeiffer binary and plain text exports \\
\hline
${\star}$ In situ XRD, NMR \& UV-Vis & \begin{tabular}[t]{@{}l@{}} - Semi-standardized file hierarchies combining \\ \quad \emph{operando} electrochemical or temperature \\ \quad data alongside characterization \end{tabular} \\
\hline
\end{tabular}
\end{table}
```

Data and metadata can be readily exported from *datalab* via the GUI or API.
Where available, *datalab* also aims to export in community-accepted standardized formats, such as the [Battery Data Format (BDF)](https://battery-data-alliance.github.io/battery-data-format/) for electrochemical cycling data, as well as exporting in generic container formats with well-reported schemas, such as JSON, CSV or HDF5.
Export to the recently standardized [ELNFileFormat](https://github.com/TheELNConsortium/TheELNFileFormat) [@ELNFileFormat] is also supported, allowing for metadata pertaining to multiple items to be provided and combined with any uploaded files in a single archive. *datalab* allows ELN exports not just of individual items or user-defined collections of items, but also of entire subgraphs of related entries to an item.

We found that one of the major barriers is actually the deployment of a system such as *datalab*; this makes adoption of any self-hosted system (such as those listed above) difficult without significant institutional support, and provides another source of vendor lock-in, even for otherwise open source projects.
To combat this, *datalab* is accompanied by a series of automated deployment rules, written as [Ansible playbooks](https://ansible.com), that can be used alongside [Terraform](https://developer.hashicorp.com/terraform)/[OpenTofu](https://opentofu.org/) to (optionally) provision a cloud server and deploy a robust *datalab* instance with encrypted offsite backups (using [Borg](https://www.borgbackup.org/)) and a full monitoring stack (using the open source [Grafana](https://grafana.com/) stack).

## Research impact statement

*datalab* is in use in a variety of academic research labs, consortia, and companies across the world.
There exists an opt-in federation, where each individual deployment is encouraged to register a (mutable) canonical URL and a prefix [datalab-org/federation](https://github.com/datalab-org/federation) in order to ensure item IDs are globally unique and to provide persistent URLs for physical labelling and data sharing via the resolver service at [purl.datalab-org.io](https://purl.datalab-org.io).
At the time of writing, there are 12 registered *datalab* instances with at least 3 others that remain unregistered, accounting for around 250 users.
Levels of engagement vary among the users, but many are using *datalab* on a near-daily basis to manage all of the data associated with their research projects.
Across the federation, we estimate that *datalab* is being used to track over ten thousand physical research objects.

In addition to the *datalab* core, a growing plugin ecosystem has developed, including plugins authored by developers outside the core team.
Digital data management with *datalab* has also enabled novel research directions, such as the creation of LLM-based AI agents to accelerate research tasks [@Jablonka2023; @Zimmermann2025].
Two examples of this, [yellowhammer](https://github.com/datalab-org/yellowhammer) [@Zimmermann2025] and [guillemot](https://github.com/datalab-org/guillemot) make use of the *datalab* API to pull in data and perform automated data curation or analysis on the behalf of a user.

# Future

While there have already been several stable releases of *datalab* over the last 5 years, *datalab* development is still active across many fronts.
We expect *datalab* to continue to scale horizontally to new domains and measurement techniques via the growing userbase and plugin ecosystem. Additionally, some broader technical changes are planned to broaden the applicability and maximize user friendliness going forward.

The technical roadmap for a *datalab* v1.0 release includes:

- A rework of the schema system for easier customizability, sharing and extension by deployments, as well as the ability to provide semantic annotations via [@Moxon2026]; this will be accommodated by a rework of the user interface to allow custom schemas to use the same user-friendly web components that exist in the core *datalab* models for rich text input and relationship tracking.
- Further improvements to the *datalab* plugin ecosystem, including enhancements of the base data block with features such as caching, offloading compute, and UI generation, providing clean interfaces to make it easier for contributors to build powerful extensions to handle arbitrary data types.
- An expansion of existing prototypes for AI-driven user interfaces, building on existing work on conversational interfaces [@Jablonka2023] and coding agents ([datalab-org/yellowhammer](https://github.com/datalab-org/yellowhammer)) [@Zimmermann2025], with the aim of allowing users to create rich and expressive pipelines via end user programming.

# AI usage disclosure

While initial development of *datalab* was done without the use of AI, recent development has made use of AI code assistants (e.g., OpenAI's Codex, Anthropic's Claude Code) in various parts of *datalab* and related development, mostly code generation for prototyping new features and interfaces.
Every pull request is still thoroughly reviewed by a human and we maintain an extensive test suite that runs on each pull request to catch regressions across the project.

AI tools were used in a limited way in the preparation of this manuscript, for proofreading and formatting only.

# Acknowledgements

M.L.E. thanks the Leverhulme Trust for funding via an Early Career Fellowship, as well as the BEWARE scheme of the Wallonia-Brussels Federation for previous funding under the European Commission's Marie Curie-Skłodowska Action (COFUND 847587).
M.L.E., J.D.B. and C.P.G. acknowledge funding from the European Union's Horizon 2020 research and innovation programme under grant agreement 957189 (DOI: 10.3030/957189), the Battery Interface Genome – Materials Acceleration Platform (BIG-MAP), where *datalab* was prototyped as an external stakeholder project.
J.D.B. was supported by the Faraday Institution CATMAT project (FIRG016) during initial development of *datalab* and is currently supported by the Welch Foundation (E-2179-20240404).

# Conflict of interest

M.L.E. is the founder and director of datalab industries ltd.

# Author contributions

M.L.E. and J.D.B. conceived the project and designed the architecture.
M.L.E. and J.D.B. implemented the first release of the software.
M.L.E., B.C., B.E.S. and J.D.B. developed and maintain the software.
M.L.E., J.D.B., G-M.R., D.W. and C.P.G. acquired funding and supervised the project.
