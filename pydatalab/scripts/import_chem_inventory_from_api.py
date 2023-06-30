import json

import numpy as np
import pandas as pd
import requests
from pymongo import MongoClient

from pydatalab.config import CONFIG

client = MongoClient(CONFIG.MONGO_URI)
db = client.datalabvue


response = requests.post(
    "https://app.cheminventory.net/api/inventorymanagement/export",
    json={
        "authtoken": CONFIG.CHEMINVENTORY_API_KEY,
    },
)


response_json = json.loads(response.text)

if response_json["status"] != "success":
    print(response)
    raise ValueError("API request to app.cheminventory.net failed")


df = pd.DataFrame(response_json["data"]["rows"])

df["type"] = "starting_materials"

df["formatted_id"] = ["X" + str(i) for i in df["id"]]

df["item_id"] = np.where(df["barcode"], df["barcode"], df["formatted_id"])
