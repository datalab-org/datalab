# Roadmap

This page collects the larger pieces of work that are planned but not yet implemented, and general areas that we expect to work on in the future.
It is a living document and is expected to be reorganised as priorities shift.
Please open an issue or reach out on the [*datalab* GitHub](https://github.com/datalab-org/datalab) if you have a use case that depends on any of the items below, or that is not yet captured here.
There are also [several issues with the 'suggestions' label](https://github.com/datalab-org/datalab/issues?q=sort%3Aupdated-desc%20is%3Aissue%20is%3Aopen%20label%3Asuggestions) across our repositories, as well as ['epics'](https://github.com/datalab-org/datalab/issues?q=sort%3Aupdated-desc+state%3Aopen+label%3A%22EPIC%22+) and ['plugin-requests'](https://github.com/datalab-org/datalab/issues?q=sort%3Aupdated-desc+state%3Aopen+label%3A%22plugin-request%22+)

## Plugin system

The plugin entry points exposed today only cover [data blocks](plugins.md). Planned extensions include:

- **Custom item types** — register new top-level item models (beyond the built-in samples, cells, and starting materials) from a plugin package.
- **Ingestion hooks** — allow plugins to register handlers that run on file upload, item creation, or other lifecycle events.
- **Webapp components** — distribute Vue components alongside the Python plugin package so that custom blocks and item types can ship their own UI.

## Other planned work

- Enhancements to the base data block lifecycle for automating caching and export with less boilerplate.
- Unification of approaches to automated data capture via remote filesystems and ["Beholder"](https://github.com/datalab-industries/datalab-beholder).
- Integration with robotic lab protocols: orchestration, execution and tracking.
- Support for Rietveld refinement in the XRD block.
- Standalone apps for certain measurement techniques that include multi-item
  comparisons.
- Structured synthesis information.
- Support for Microscopy data analysis and visualisation.
