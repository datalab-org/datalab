# Draft design: Data block lifecycle

Here is a current idea for how data should flow through a datablock.
The main design constraint is that it should be possible for non-expert
developers to easily define a new block that can parse and display valid data,
returning errors where appropriate.

In the best case scenario, this would mean that the block developer should not
need to write any Javascript, Bokeh or pydantic code, unless they want to do
something more advanced.

The default data model and set of hooks must then be sufficient to encapsulate
simple use cases, in order of priority:

1. Provided a single file from the UI, perform an operation on the file, store
  the result and create a plot to be shown in the UI.
2. Provided multiple files from the UI, parse them according to some rule and
   create a plot to be shown in the UI.
3. Provided multiple blocks or data entries, create a comparative plot.


<style>
    .route > rect{
        fill:#FF0000;
        stroke:#FFFF00;
        stroke-width:4px;
    }
</style>

```mermaid
graph
    A[Data introduced] --> B["parse_metadata()"]
    A --> L("original file stored \n(datalake)")
    B --> B2{"Metadata\nModel"}
    B --> D["parse_data()"]
    B2 --> X("store in db \n(blocks collection) ")
    D --> D2{"Data\nModel"}
    D2 --> E("store (gridFS/pickle)")
    E --> F["featurize_data()"] --> X
    E --> G["create_preview()"] --> X
    E --> H["plot_functions()"] --> X
    X --> Z["serve to webapp"]
    E --> Z
```
