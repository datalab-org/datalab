# Advanced search

The tables of the web app (samples, starting materials, equipment, collections, and, for
administrators, users and groups) can be searched on the server with filters written in the
[OPTIMADE filter language](https://www.optimade.org/specification/latest/#api-filtering-format-specification),
e.g.

```
name CONTAINS "LFP" AND date >= "2026-01-01T00:00:00Z"
```

Only the filter language is used: *datalab* does not serve an OPTIMADE API, and searches only
run against its own database.

## API

| Route | Returns |
| --- | --- |
| `GET /query/types?data_type=<table>` | The types a web app table can search, e.g. samples and cells for the samples table. |
| `GET /query/<type>/schema` | The properties of a type that filters can use, with their operators. |
| `GET /query/<type>?filter=...` | The IDs of the entries of a type matching `filter`, with `total` and `next_offset`. |

Searches take `sort` (comma-separated properties, `-` for descending), `limit` (at most 1000),
`offset`, and `mine=true` to keep only entries the current user created. Results respect the
usual permissions, and only identify the matching entries: the web app shows the matching rows
from the table data it already has.

Filters are parsed with the grammar of
[`optimade-python-tools`](https://github.com/Materials-Consortia/optimade-python-tools) and
compiled to MongoDB queries restricted to the properties listed in the type's schema. Invalid
filters, and properties that cannot be searched, return a `400` error with the reason.

## Web app

The search box of a table offers:

- **Quick filters** ("My items", "Latest items", "Active", "Have blocks"): presets that add an
  OPTIMADE filter, or `mine=true`, to the search, defined in `webapp/src/quickSearchOptions.js`.
- **Custom filter**: a query builder that writes an OPTIMADE filter for one type, which can also
  be edited by hand. Quick filters and the custom filter are combined with `AND`.
- **Group by**: groups the table's rows by one or more fields (type, creators, status, date by
  day, week, month or year, tags, and the groupable properties of the schema), nesting one level
  of groups per field. Groups are shown as collapsible headers within the table, which keeps its
  columns, filters, sorting, selection and paginator; the paginator pages through the headers
  and the rows of the open groups. An item with several tags or creators is listed under each of
  them, and selecting it in one group selects it everywhere.
