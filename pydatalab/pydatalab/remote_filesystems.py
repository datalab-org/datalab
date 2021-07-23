import datetime
import json
import os
import subprocess

from pymongo import MongoClient

from pydatalab.resources import DIRECTORIES

# from fs.smbfs import SMBFS


client = MongoClient("mongodb://localhost:27017/")
db = client.datalabvue

FILESYSTEMS_COLLECTION = db["remoteFilesystems"]


def get_directory_structure_json(directory_path):
    process = subprocess.Popen(
        ["tree", "-Jhf", "--timefmt", "%Y-%m-%d %H:%M:%S %Z", directory_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()

    dir_structure = json.loads(stdout)
    # because we used tree -f, the name: fields all contain full paths. We want to do a little re-arranging
    # so we get both a name, and a relative path field
    fix_tree_paths(dir_structure[0]["contents"], directory_path)
    dir_tree = dir_structure[0]["contents"]

    return dir_tree


def fix_tree_paths(subtree_list, root_path):
    for subtree in subtree_list:
        full_path = subtree["name"]
        path, filename = os.path.split(full_path)

        relative_path = os.path.relpath(path, start=root_path)
        if relative_path == ".":
            relative_path = "/"
        else:
            relative_path = "/" + relative_path + "/"

        subtree["relative_path"] = relative_path
        subtree["name"] = filename
        if "contents" in subtree:
            fix_tree_paths(
                subtree["contents"], root_path
            )  # recursively make changes throughout the  tree


def save_directory_structure_to_db(directory_name, dir_structure):
    result = FILESYSTEMS_COLLECTION.update_one(
        {"name": directory_name},
        {
            "$set": {
                "contents": dir_structure,
                "last_updated": datetime.datetime.now().isoformat(),
                "type": "toplevel",
            }
        },
        upsert=True,
    )
    print("Result of saving directory structure to the db:")
    print(result.raw_result)


def get_cached_directory_structure_from_db(directory_name):
    return FILESYSTEMS_COLLECTION.find_one({"name": directory["name"]})


def get_all_directory_structures(directories=DIRECTORIES):
    all_directory_structures = []
    for directory in directories:
        print(f"Retrieving remote directory {directory['name']} at {directory['path']}")
        try:
            dir_structure = get_directory_structure_json(directory["path"])
            save_directory_structure_to_db(directory["name"], dir_structure)
        except (json.JSONDecodeError, KeyError):
            print("Error reading remote filetree json.")
            dir_structure = [{"type": "error", "name": "Could not reach remote server"}]

        wrapped_dir_structure = {
            "name": directory["name"],
            "type": "toplevel",
            "contents": dir_structure,
        }

        all_directory_structures.append(wrapped_dir_structure)

    return all_directory_structures


def get_cached_directory_structures(directories=DIRECTORIES):
    all_directory_structures = []
    for directory in directories:
        wrapped_dir_structure = FILESYSTEMS_COLLECTION.find_one({"name": directory["name"]})
        if not wrapped_dir_structure:
            wrapped_dir_structure = {
                "name": directory["name"],
                "type": "toplevel",
                "last_updated": None,
                "contents": [
                    {
                        "type": "error",
                        "name": "Cached directory structure not found in the db",
                    }
                ],
            }
        all_directory_structures.append(wrapped_dir_structure)

    return all_directory_structures


## An alternate way to connect...
# def connect_to_grey_instrument_fs():
#    # the server is at smb://diskhost-c.ch.private.cam.ac.uk, but that doesn't seem to work with fs.smbfs. I got the IP using:
#    # smbutil status diskhost-c.ch.private.cam.ac.uk
#    smb_fs = SMBFS(
#       "172.26.122.189", username=USERNAME, domain="AD", passwd=PASSWORD, direct_tcp=True
#    )

#    return smb_fs.opendir('/greygroup-instruments/')
