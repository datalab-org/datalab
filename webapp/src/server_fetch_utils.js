// utility functions to deal with fetch server calls
// all code using fetch should be collected into this file

import store from "@/store/index.js";
import { API_URL } from "@/resources.js";

// ****************************************************************************
// A simple wrapper to simplify response handling for fetch calls
// ****************************************************************************

// eslint-disable-next-line no-unused-vars
function fetch_get(url) {
  const requestOptions = {
    method: "GET",
  };
  return fetch(url, requestOptions).then(handleResponse);
}

function fetch_post(url, body, headers = { "Content-Type": "application/json" }) {
  const requestOptions = {
    method: "POST",
    headers: headers,
    body: JSON.stringify(body),
  };
  return fetch(url, requestOptions).then(handleResponse);
}

// eslint-disable-next-line no-unused-vars
function fetch_put(url, body) {
  const requestOptions = {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
  return fetch(url, requestOptions).then(handleResponse);
}

// eslint-disable-next-line no-unused-vars
function fetch_delete(url) {
  const requestOptions = {
    method: "DELETE",
  };
  return fetch(url, requestOptions).then(handleResponse);
}

function handleResponse(response) {
  return response.text().then((text) => {
    console.log("fetch was successful");
    console.log(response);
    const data = text && JSON.parse(text);

    if (!response.ok) {
      const error = (data && data.message) || response.statusText;
      return Promise.reject(error);
    }

    return data;
  });
}

// ****************************************************************************
// exported functions
// ****************************************************************************

export function createNewSample(sample_id, date, name) {
  return fetch_post(`${API_URL}/new-sample/`, {
    sample_id: sample_id,
    date: date,
    name: name,
  }).then(function (response_json) {
    console.log("received the following data from fetch new-sample:");
    console.log(response_json.sample_list_entry);
    console.log(`sample_id: ${sample_id}`);
    store.commit("appendToSampleList", response_json.sample_list_entry);
    // store.commit('createSampleData', {
    // 	"sample_id": sample_id,
    // 	"sample_data": response_json.sample_data
    // });
    return "success";
  });
}

export function getSampleList() {
  return fetch_get(`${API_URL}/samples`)
    .then(function (response_json) {
      store.commit("setSampleList", response_json.samples);
    })
    .catch((error) => {
      console.error("Error when fetching sample list");
      console.error(error);
      throw error;
    });
}

export function getStartingMaterialList() {
  return fetch_get(`${API_URL}/starting-materials`)
    .then(function (response_json) {
      store.commit("setStartingMaterials", response_json.items);
    })
    .catch((error) => {
      console.error("Error when fetching starting material list");
      console.error(error);
      throw error;
    });
}

export function deleteSample(sample_id, sample_summary) {
  return fetch_post(`${API_URL}/delete-sample/`, {
    sample_id: sample_id,
  })
    .then(function (response_json) {
      console.log("delete successful" + response_json);
      store.commit("deleteFromSampleList", sample_summary);
    })
    .catch((error) => alert("Sample delete failed for " + sample_id + ": " + error));
}

export async function getSampleData(sample_id) {
  return fetch_get(`${API_URL}/get_sample_data/${sample_id}`)
    .then((response_json) => {
      console.log(response_json);
      store.commit("createSampleData", {
        sample_id: sample_id,
        sample_data: response_json.sample_data,
      });
      store.commit("updateFiles", response_json.files_data);

      return "success";
    })
    .catch((error) => alert("Error getting sample data: " + error));
}

export async function updateBlockFromServer(sample_id, block_id, block_data) {
  // var block = store.getters.getBlockBySampleIDandBlockID(sample_id, block_id)
  console.log("updateBlockFromServer called with data:");
  console.log(block_data);
  store.commit("setBlockUpdating", block_id);
  return fetch_post(`${API_URL}/update-block/`, {
    sample_id: sample_id,
    block_id: block_id,
    block_data: block_data,
  })
    .then(function (response_json) {
      store.commit("updateBlockData", {
        sample_id: sample_id,
        block_id: block_id,
        block_data: response_json.new_block_data,
      });
    })
    .catch((error) => alert("Error in updateBlockFromServer: " + error))
    .then(() => store.commit("setBlockNotUpdating", block_id));
}

export function addABlock(sample_id, block_kind, index = null) {
  console.log("addABlock called with", sample_id, block_kind);
  var block_id_promise = fetch_post(`${API_URL}/add-data-block/`, {
    sample_id: sample_id,
    block_kind: block_kind,
    index: index,
  })
    .then(function (response_json) {
      // The payload could probably just be response_json instead of making a new object...
      store.commit("addABlock", {
        sample_id: sample_id,
        new_block_obj: response_json.new_block_obj,
        new_display_order: response_json.new_display_order,
      });
      return response_json.new_block_obj.block_id;
    })
    .catch((error) => console.error("Error in addABlock:", error));
  return block_id_promise;
}

export function saveSample(sample_id) {
  console.log("saveSample Called!");
  var sample_data = store.getters.getSample(sample_id);

  fetch_post(`${API_URL}/save-sample/`, {
    sample_id: sample_id,
    data: sample_data,
  })
    .then(function (response_json) {
      if (response_json.status == "success") {
        // this should always be true if you've gotten this far...
        console.log("Save successful!");
        store.commit("setSaved", { sample_id: sample_id, isSaved: true });
      }
    })
    .catch(function (error) {
      alert("Save unsuccessful :(", error);
    });
}

export function deleteBlock(sample_id, block_id) {
  console.log("deleteBlock called!");
  fetch_post(`${API_URL}/delete-block/`, {
    sample_id: sample_id,
    block_id: block_id,
  })
    // eslint-disable-next-line no-unused-vars
    .then(function (response_json) {
      // response_json should always just be {status: "success"}, so we don't actually use it
      store.commit("removeBlockFromDisplay", {
        sample_id: sample_id,
        block_id: block_id,
      });
      // currently, we don't actually delete the block from the store, so it may get re-added to the db on the next save. Fix once new schemas are established
    })
    .catch((error) => alert(`Delete unsuccessful :(\n error: ${error}`));
}

export function deleteFileFromSample(sample_id, file_id) {
  console.log("deleteFileFromSample called with sample_id and file_id:");
  console.log(sample_id);
  console.log(file_id);
  fetch_post(`${API_URL}/delete-file-from-sample/`, {
    sample_id: sample_id,
    file_id: file_id,
  })
    .then(function (response_json) {
      store.commit("removeFileFromSample", {
        sample_id: sample_id,
        file_id: file_id,
      });
      store.commit("updateFiles", response_json.new_file_obj);
    })
    .catch((error) => alert(`Delete unsuccessful :(\n error: ${error}`));
}

export async function fetchRemoteTree() {
  console.log("fetchRemoteTree called!");
  return fetch_get(`${API_URL}/list-remote-directories/`).then(function (response_json) {
    store.commit("setRemoteDirectoryTree", response_json);
    return response_json;
  });
}

export async function fetchCachedRemoteTree() {
  console.log(`fetchCachedRemoteTree called! on ${API_URL}/list-remote-directories-cached/`);
  return fetch_get(`${API_URL}/list-remote-directories-cached/`).then(function (response_json) {
    store.commit("setRemoteDirectoryTree", response_json.cached_dir_structures);
    return response_json;
  });
}

export async function addRemoteFileToSample(file_entry, sample_id) {
  console.log("loadSelectedRemoteFiles");
  return fetch_post(`${API_URL}/add-remote-file-to-sample/`, {
    file_entry: file_entry,
    sample_id: sample_id,
  })
    .then(function (response_json) {
      //handle response
      console.log("received remote sample!");
      console.log(response_json);
      store.commit("updateFiles", {
        [response_json.file_id]: response_json.file_information,
      });
      if (!response_json.is_update) {
        store.commit("addFileToSample", {
          sample_id: sample_id,
          file_id: response_json.file_id,
        });
      }
    })
    .catch((error) => `addRemoteFilesToSample unsuccessful. Error: ${error}`);
}

// export async function addRemoteFilesToSample(file_entries, sample_id) {
// 	console.log('loadSelectedRemoteFiles')
// 	return fetch_post(`${API_URL}/add-remote-files-to-sample/`, {
// 		file_entries: file_entries,
// 		sample_id: sample_id,
// 	}).then( function(response_json) {
// 		//handle response
// 		console.log("received remote samples!")
// 		console.log(response_json)
// 	}).catch( error => (`addRemoteFilesToSample unsuccessful. Error: ${error}`))
// }
