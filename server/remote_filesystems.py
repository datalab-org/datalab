import subprocess
import json
import os
import shutil

from resources import DIRECTORIES, DIRECTORIES_DICT
# from fs.smbfs import SMBFS

def get_directory_structure_json(directory_path):
   process = subprocess.Popen(['tree', '-Jhf','--timefmt',"%Y-%m-%d %H:%M:%S %Z", directory_path],
      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   stdout, stderr = process.communicate()

   dir_structure = json.loads(stdout)

   # because we used tree -f, the name: fields all contain full paths. We want to do a little re-arranging
   # so we get both a name, and a relative path field
   fix_tree_paths(dir_structure[0]["contents"], directory_path)

   return dir_structure

def fix_tree_paths(subtree_list, root_path):
   for subtree in subtree_list:
      full_path = subtree["name"]
      path, filename = os.path.split(full_path)

      relative_path =  os.path.relpath(path, start=root_path)
      if relative_path == ".": relative_path = "/"
      else: relative_path = "/" + relative_path + "/"

      subtree["relative_path"] = relative_path
      subtree["name"] = filename
      if "contents" in subtree:
         fix_tree_paths(subtree["contents"], root_path) # recursively make changes throughout the  tree


def get_all_directory_structures(directories=DIRECTORIES):
   all_directory_structures = []
   for directory in directories:
      print(f"Retrieving remote directory {directory['name']} at {directory['path']}")
      try: 
         dir_structure=get_directory_structure_json(directory["path"])[0]["contents"]
      except json.JSONDecodeError:
         print("JSON decode error")
         dir_structure = [{"type":"error", "name":"JSON decode error"}]

      wrapped_dir_structure = {
         "name": directory["name"],
         "type": "toplevel",
         "contents": dir_structure,
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





