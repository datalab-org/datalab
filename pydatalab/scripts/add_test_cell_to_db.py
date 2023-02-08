from pymongo import MongoClient, uri_parser

from pydatalab.config import CONFIG
from pydatalab.models import Cell

client = MongoClient(CONFIG.MONGO_URI)
database = uri_parser.parse_uri(CONFIG.MONGO_URI).get("database")
db = client.datalabvue

new_cell = Cell(
    **{
        "item_id": "test_cell",
        "name": "test cell",
        "date": "1970-02-01",
        "anode": [
            {
                "item": {"item_id": "test", "chemform": "Li15Si4", "type": "samples"},
                "quantity": 2.0,
                "unit": "mg",
            },
            {
                "item": {"item_id": "test", "chemform": "C", "type": "samples"},
                "quantity": 2.0,
                "unit": "mg",
            },
        ],
        "cathode": [
            {
                "item": {"item_id": "test_cathode", "chemform": "LiCoO2", "type": "samples"},
                "quantity": 2000,
                "unit": "kg",
            }
        ],
        "cell_format": "swagelok",
        "type": "cells",
    }
)


db.items.insert_one(new_cell.dict())
