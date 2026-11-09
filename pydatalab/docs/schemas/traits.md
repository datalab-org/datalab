# Traits

The item models in *datalab* are assembled from **traits**: small mixin models that each
contribute a related group of fields.
Rather than every item type redeclaring who owns it
or which collections it belongs to, it inherits the corresponding trait.

::: pydatalab.models.traits
    options:
        inherited_members: false
