# Identifiers

There are three ways of identifiying items in datalab, each with different
traits and objectives:

| Identifier Name | Uniqueness | Mutability | Description | Examples |
|:---------------:|:----------:|:----------:|:------------|:---------|
| `refcode`       | Global     | Immutable | A short immutable string that is unique across all items in the database; the `refcode` is prefixed with a deployment tag, which itself is registered and unique across all datalab deployments. Each group can enforce its own scheme for refcodes (see examples). This is the ID that should be used in the API for referring to items, and is also the ID that should be preferred when crossing between deployments. | `grey:ABACUF`, `grey:123456`, `bocarsly:A` |
| `item_id` | Local | Mutable | A meaningful human-readable identifier for the sample/item. This can be any string and can be used to encode arbitrary metadata in a user-specific short-hand, comparable to what may be written on a vial in the lab. | `jdb-LNO-1-2-4p5V`, `me388_c1_e2` |
| `immutable_id` | Local, per data type | Immutable | The underlying ID used in the database backend. |
