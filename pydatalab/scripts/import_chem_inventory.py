import random

import pandas as pd
from pymongo import MongoClient

from pydatalab.config import CONFIG
from pydatalab.models import StartingMaterial


def generate_random_startingmaterial_id():
    """
    This function generates XX + a random 15-length string for use as an id for starting materials
    that don't have a barcode.
    """

    randlist = ["XX"] + random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=15)

    return "".join(randlist)


client = MongoClient(CONFIG.MONGO_URI)

db = client.datalabvue
data_collection = db.items


df = pd.read_excel("greyGroup_chemInventory_7Oct21.xlsx")
df["type"] = "starting_materials"  # all starting materials will have this as the type
df["item_id"] = df["Barcode"]  # assign item_id to be the Barcode by default

# some starting materials don't have a barcode. Create a random id for those.
replacement_dict = {
    i: generate_random_startingmaterial_id() for i, _ in df[df.item_id.isna()].iterrows()
}
df.item_id.fillna(value=replacement_dict, inplace=True)

# clean the molecular weight column:
df["Molecular Weight"].replace(" ", float("nan"), inplace=True)

# convert df to list of dictionaries for ingestion into mongo
df.to_dict(orient="records")

# filter out missing values
ds = [
    {k: v for k, v in d.items() if (v != "None" and pd.notnull(v))}
    for d in df.to_dict(orient="records")
]


starting_materials = [StartingMaterial(**d) for d in ds]

# update or insert all starting materials
for starting_material in starting_materials:
    print(f"adding starting material {starting_material.item_id} ({starting_material.name})")
    result = data_collection.update_one(
        {"item_id": starting_material.item_id}, {"$set": starting_material.dict()}, upsert=True
    )
