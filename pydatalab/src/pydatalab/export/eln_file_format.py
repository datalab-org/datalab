"""An implementation of exporters from datalab to the RO-Crate-based
[ELNFileFormat](https://github.com/TheELNConsortium/TheELNFileFormat).
"""

from pydatalab.models import Item, ITEM_MODELS

class ELNFileExporter:
    
    @classmethod
    def from_item(cls, item_data: Item):

        model = ITEM_MODELS.get(item_data.type)

        if model is None:
            raise ValueError(f"Unsupported item type: {item_data.type}")

        # Load data into model class
        item = model(**item_data.dict())

        return item
