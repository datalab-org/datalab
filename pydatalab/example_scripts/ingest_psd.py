import collections
import datetime
import getpass

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

API_URL = "https://api-dev.odbx.science"
user = input("Enter a username: ")
pw = getpass.getpass()
AUTH = HTTPBasicAuth(user, pw)


def read_mythen_log(fname):
    df = pd.read_csv(fname, comment="#")
    id_pattern_map = collections.defaultdict(list)

    file_list = df["file_number"].to_list()
    for ind, sample_id in enumerate(df["sample_id"].to_list()):
        id_pattern_map[sample_id.strip()].append(file_list[ind])

    id_pattern_map = dict(id_pattern_map)

    return id_pattern_map, df


def collect_samples_from(fname):
    df = pd.read_csv(fname, comment="#")

    samples = {}

    for ind, row in df.iterrows():
        row = dict(row)
        _id = row["User CRSID"] + "-" + row["Capillary ID"]
        sample = {
            "type": "samples",
            "date": str(datetime.datetime(2022, 9, 14, 9, 0, 0, 0)),
            "description": row["Composition"]
            + "\nThis sample was provided for the 14/09/2022 BAG time at DLS i11.",
            "item_id": _id,
            "name": row["Capillary ID"],
            "chemform": None,
        }
        samples[_id] = sample
    return samples


def upload_patterns_and_files(samples, id_pattern_map):
    unmeasured_samples = set()
    for sample in samples.values():
        sample_id = sample["item_id"]
        name = sample["name"]
        if name not in id_pattern_map:
            unmeasured_samples.add(name)
            continue
        else:
            print(f"Found patterns for {name}")

        response = requests.post(f"{API_URL}/new-sample/", json=sample, auth=AUTH)
        if response.status_code not in (201, 409):
            raise RuntimeError(f"Unable to add sample: {response}")
        for _f in id_pattern_map[name]:
            fname = f"{_f}-mythen_summed.dat"
            file_entry = {
                "toplevel_name": "Diamond Light Source/i11/cy28349-12",
                "name": fname,
                "relative_path": ".",
                "time": None,
                "size": None,
            }

            body = {
                "file_entry": file_entry,
                "item_id": sample_id,
            }

            response = requests.post(f"{API_URL}/add-remote-file-to-sample/", json=body, auth=AUTH)

            if response.status_code not in (200, 201, 409):
                breakpoint()
                raise RuntimeError(
                    f"Unable to add file {fname} to sample {sample_id}: {response.content}"
                )

    print(f"No patterns found for samples {unmeasured_samples}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--log-file", type=str)
    parser.add_argument("--sample-list", type=str)

    args = vars(parser.parse_args())

    id_pattern_map, log_df = read_mythen_log(args["log-file"])
    samples = collect_samples_from(args["sample-list"])

    upload_patterns_and_files(samples, id_pattern_map)
