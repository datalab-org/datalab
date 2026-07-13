# Overview

*datalab*'s block system provides a modular approach to data processing and visualisation.
Each block type is a specialised component that handles specific kinds of data and operations, making it easy to extend the system's capabilities without modifying the core architecture.
Typically, a given technique (e.g., XRD, NMR) will have its own block.
Blocks can be implemented either in the main package, or as a plugin (see ["Plugins"](../plugins.md)).

Data blocks are modular components that:

1. Process specific file types and data formats for a technique or set of techniques,
2. Generate visualisations and plots from this data to be shown in the UI,
3. Store and manage their own state persistently in a database,
4. Can be attached to individual items or collections in your data management system,
5. Provide a mechanism for handling "events" through a decorator-based registration system,
6. Expose a consistent API for creation, updating, and deletion.
7. Handle logging, errors and warnings in a consistent way to show in the UI.

## Block lifecycle

1. **Creation**: Blocks are instantiated with an item or collection ID
2. **Initialization**: Initial state is set up, potentially including file data and defaults
3. **Processing**: Data is processed, plots are generated, and state is updated
4. **Serialization**: Block state is serialized for storage or transmission
5. **Update**: Blocks can receive updates from the web interface
6. **Deletion**: Blocks can be removed from items or collections


## Web API

The block system exposes several API endpoints:

- `/add-data-block/`: Create and add a new block to an item
- `/update-block/`: Update an existing block's state
- `/delete-block/`: Remove a block from an item

## Creating a new block

To create a new block type:

1. Create a class that inherits from `DataBlock`
2. Define the accepted file extensions and block metadata (descriptions will be used to populate the UI documentation automatically)-
3. Implement data processing and visualization methods, with e.g., JSON-serialized Bokeh plots stored in the `self.data["bokeh_plot_data"]` attribute
4. Any data to be stored in the database can be defined in the `self.data` attribute
5. Register any event handlers using the `@event` decorator
5. Add the block type to the `BLOCK_TYPES` registry

By default, a generic UI component will be used in the *datalab* interface that
will make use of titles, descriptions, accepted file extensions to render a
simple user interface for the block.
When the user loads the block in the UI, the block's `plot_functions` methods
will be called in turn, which will either load from scratch, or load cached data
for that block.
If a JSON-serialized Bokeh plot is found in the block's data, this will be
rendered in the UI.

## Event system

The event system allows external functions to be called by name, enabling clean interaction between the frontend and server-side block functionality.
This is a new feature and this documentation will evolve alongside it.

Currently, the event system allows:

- Registration of event handlers in Python via the `@event` decorator
- Access to available events at both class and instance levels
- Runtime dispatch of events based on name
- Support for event parameters passed as keyword arguments
- Events can then be triggered by the front-end; for example, a Bokeh-based block can trigger an event in a Bokeh callback using the [`CustomEvent`](https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent/CustomEvent) API, for example:
  ```javascript
    const event = new CustomEvent("block-event", {
        detail: {
            block_id: '<block_id>',
            event_name: '<event_name>',
            state_data: '<some data>',
        },
        bubbles: true
    });
    document.dispatchEvent(event);
  ```
  The base data block (`DataBlockBase.vue`) will listen for such events registered as `'block-event'` and pass them to the appropriate server-side block.
  An example callback generator for an event consisting of a single parameter
  update can be found at [`generate_js_callback_single_float_parameter`][pydatalab.blocks.base.generate_js_callback_single_float_parameter].

## Asynchronous processing (EXPERIMENTAL)

!!! warning
    This feature is experimental and may change in future releases.

By default, block processing is synchronous: the `/update-block/` endpoint processes the block inline and returns the result in a single response.
For blocks that handle large datasets (e.g., parsing multi-megabyte Excel files into Bokeh plots), this can tie up a server thread for a long time.

The async processing backend moves this work to a background thread pool.
When enabled, the `/update-block/` endpoint returns immediately with a `202 Accepted` response containing a `task_id` and `status_url`.
The frontend then polls the status endpoint until the result is ready.

### Enabling async processing

Add the block type slugs you want to process asynchronously to the `ASYNC_BLOCK_TYPES` list in your server config (JSON config file or environment variable):

```json
{
  "ASYNC_BLOCK_TYPES": ["cycle", "xrd"]
}
```

Or via environment variable:

```bash
export PYDATALAB_ASYNC_BLOCK_TYPES='["cycle", "xrd"]'
```

Block types not in this list continue to be processed synchronously.
Individual block classes can also opt in by setting `_prefers_async = True` as a class attribute.

### How it works

1. The client sends an `/update-block/` request as usual.
2. If the block type is in `ASYNC_BLOCK_TYPES` (or has `_prefers_async = True`), the server creates a task record, schedules a background job, and returns `202` with `{"task_id": "...", "status_url": "/blocks/<task_id>/status"}`.
3. The background worker processes the block, writing intermediate progress stages to the task record so the frontend can display them.
4. The processed block data is written to a GridFS transfer buffer keyed by task ID. The block state is also persisted to the item's `blocks_obj` as usual.
5. When the client polls the status endpoint and the task is `READY`, the response includes the full block data from GridFS.
The GridFS entry is deleted on delivery.
6. A periodic cleanup job handles timed-out tasks (default: 1 hour) and purges old completed tasks and any orphaned GridFS data (default: 6 hours).

### Deployment considerations

Each gunicorn worker runs its own single-thread executor, so jobs are processed by whichever worker received the request.
CPU-bound block processing still contends with the GIL within a worker.
For deployments with heavy processing loads, scaling via additional gunicorn workers (rather than threads) is recommended.
A periodic cleanup job runs independently in each worker to purge stale tasks and orphaned GridFS data; the cleanup logic is idempotent so this is safe.

## Future directions

Future updates to the block system will focus on:

- Reducing boilerplate code required for new block types.
- Enhanced automatic caching after block creation.
- Improving the event system to enable richer UI interactions, e.g,. setting user parameters or controlling default plot styles.
- Providing better support for custom user interfaces (i.e., allowing plugins to also specify custom Vue code).
- Evolving the async backend so that each processing stage (file parsing, visualisation generation, database writes) runs as an independent task in a pipeline, enabling finer-grained progress reporting, per-stage retries, and better utilisation of multi-core servers via process-based workers.
