// utility functions to deal with fetch server calls
// all code using fetch should be collected into this file

import store from "@/store/index.js";
import { API_URL, API_TOKEN } from "@/resources.js";

// ****************************************************************************
// A simple wrapper to simplify response handling for fetch calls
// ****************************************************************************
export function construct_headers(additional_headers = null) {
  let headers = {};
  if (additional_headers != null) {
    headers = additional_headers;
  }
  if (API_TOKEN != null && API_TOKEN != "") {
    headers["Authorization"] = API_TOKEN;
  }
  return headers;
}

// eslint-disable-next-line no-unused-vars
function fetch_get(url) {
  const requestOptions = {
    method: "GET",
    headers: construct_headers(),
    credentials: "include",
  };
  return fetch(url, requestOptions).then(handleResponse);
}

function fetch_post(url, body) {
  let headers = construct_headers({ "Content-Type": "application/json" });
  const requestOptions = {
    method: "POST",
    headers: headers,
    body: JSON.stringify(body),
    credentials: "include",
  };
  return fetch(url, requestOptions).then(handleResponse);
}

// eslint-disable-next-line no-unused-vars
function fetch_put(url, body) {
  let headers = construct_headers({ "Content-Type": "application/json" });
  const requestOptions = {
    method: "PUT",
    headers: headers,
    body: JSON.stringify(body),
    credentials: "include",
  };
  return fetch(url, requestOptions).then(handleResponse);
}

// eslint-disable-next-line no-unused-vars
function fetch_delete(url) {
  let headers = construct_headers({ "Content-Type": "application/json" });
  const requestOptions = {
    method: "DELETE",
    headers: headers,
    credentials: "include",
  };
  return fetch(url, requestOptions).then(handleResponse);
}

function handleResponse(response) {
  return response.text().then((text) => {
    console.log("fetch was successful");
    console.log(response);
    console.log(text);
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

// eslint-disable-next-line no-unused-vars
export function createNewSample(item_id, date, name, startingData = {}, copyFrom = null) {
  return fetch_post(`${API_URL}/new-sample/`, {
    copy_from_item_id: copyFrom,
    new_sample_data: {
      item_id: item_id,
      date: date,
      name: name,
      ...startingData,
    },
  }).then(function (response_json) {
    console.log("received the following data from fetch new-sample:");
    console.log(response_json.sample_list_entry);
    console.log(`item_id: ${item_id}`);
    store.commit("prependToSampleList", response_json.sample_list_entry);
    // store.commit('createSampleData', {
    //  "item_id": item_id,
    //  "sample_data": response_json.sample_data
    // });
    return "success";
  });
}

export function createNewSamples(newSampleDatas, copyFromItemIds = null) {
  return fetch_post(`${API_URL}/new-samples/`, {
    copy_from_item_ids: copyFromItemIds,
    new_sample_datas: newSampleDatas,
  }).then(function (response_json) {
    console.log("received the following data from fetch new-samples:");
    console.log(response_json);

    response_json.responses.forEach((response) => {
      if (response.status == "success") {
        store.commit("appendToSampleList", response.sample_list_entry);
      }
    });

    return response_json.responses;
  });
}

export function getSampleList() {
  return fetch_get(`${API_URL}/samples/`)
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
  return fetch_get(`${API_URL}/starting-materials/`)
    .then(function (response_json) {
      store.commit("setStartingMaterialList", response_json.items);
    })
    .catch((error) => {
      console.error("Error when fetching starting material list");
      console.error(error);
      throw error;
    });
}

export function searchItems(query, nresults = 100, types = null) {
  // construct a url with parameters:
  var url = new URL(`${API_URL}/search-items/`);
  var params = { query: query, nresults: nresults, types: types };
  Object.keys(params).forEach((key) => url.searchParams.append(key, params[key]));
  console.log(`using to construct url for searchItems: ${url}`);
  console.log(url);
  console.log(params);
  return fetch_get(url).then(function (response_json) {
    return response_json.items;
  });
}

export async function getUserInfo() {
  return fetch_get(`${API_URL}/get-current-user/`)
    .then((response_json) => {
      return response_json;
    })
    .catch(() => {
      return null;
    });
}

export function searchUsers(query, nresults = 100) {
  // construct a url with parameters:
  var url = new URL(`${API_URL}/search-users/`);
  var params = { query: query, nresults: nresults };
  Object.keys(params).forEach((key) => url.searchParams.append(key, params[key]));
  console.log(`using to construct url for searchUsers: ${url}`);
  console.log(url);
  console.log(params);
  return fetch_get(url).then(function (response_json) {
    return response_json.users;
  });
}

export function deleteSample(item_id, sample_summary) {
  return fetch_post(`${API_URL}/delete-sample/`, {
    item_id: item_id,
  })
    .then(function (response_json) {
      console.log("delete successful" + response_json);
      store.commit("deleteFromSampleList", sample_summary);
    })
    .catch((error) => alert("Sample delete failed for " + item_id + ": " + error));
}

export async function getItemData(item_id) {
  return fetch_get(`${API_URL}/get-item-data/${item_id}`)
    .then((response_json) => {
      console.log(response_json);
      store.commit("createItemData", {
        item_id: item_id,
        item_data: response_json.item_data,
        child_items: response_json.child_items,
        parent_items: response_json.parent_items,
      });
      store.commit("updateFiles", response_json.files_data);

      return "success";
    })
    .catch((error) => alert("Error getting sample data: " + error));
}

export async function updateBlockFromServer(item_id, block_id, block_data) {
  console.log("updateBlockFromServer called with data:");
  console.log(block_data);
  store.commit("setBlockUpdating", block_id);
  return fetch_post(`${API_URL}/update-block/`, {
    item_id: item_id,
    block_id: block_id,
    block_data: block_data,
  })
    .then(function (response_json) {
      store.commit("updateBlockData", {
        item_id: item_id,
        block_id: block_id,
        block_data: response_json.new_block_data,
      });
    })
    .catch((error) => alert("Error in updateBlockFromServer: " + error))
    .then(() => store.commit("setBlockNotUpdating", block_id));
}

export function addABlock(item_id, block_type, index = null) {
  console.log("addABlock called with", item_id, block_type);
  var block_id_promise = fetch_post(`${API_URL}/add-data-block/`, {
    item_id: item_id,
    block_type: block_type,
    index: index,
  })
    .then(function (response_json) {
      store.commit("addABlock", {
        item_id: item_id,
        new_block_obj: response_json.new_block_obj,
        new_block_insert_index: response_json.new_block_insert_index,
      });
      return response_json.new_block_obj.block_id;
    })
    .catch((error) => console.error("Error in addABlock:", error));
  return block_id_promise;
}

export function saveItem(item_id) {
  console.log("saveItem Called!");
  var item_data = store.state.all_item_data[item_id];
  fetch_post(`${API_URL}/save-item/`, {
    item_id: item_id,
    data: item_data,
  })
    .then(function (response_json) {
      if (response_json.status === "success") {
        // this should always be true if you've gotten this far...
        console.log("Save successful!");
        store.commit("setSaved", { item_id: item_id, isSaved: true });
      }
    })
    .catch(function (error) {
      alert("Save unsuccessful :(", error);
    });
}

export function deleteBlock(item_id, block_id) {
  console.log("deleteBlock called!");
  fetch_post(`${API_URL}/delete-block/`, {
    item_id: item_id,
    block_id: block_id,
  })
    // eslint-disable-next-line no-unused-vars
    .then(function (response_json) {
      // response_json should always just be {status: "success"}, so we don't actually use it
      store.commit("removeBlockFromDisplay", {
        item_id: item_id,
        block_id: block_id,
      });
      // currently, we don't actually delete the block from the store, so it may get re-added to the db on the next save. Fix once new schemas are established
    })
    .catch((error) => alert(`Delete unsuccessful :(\n error: ${error}`));
}

export function deleteFileFromSample(item_id, file_id) {
  console.log("deleteFileFromSample called with item_id and file_id:");
  console.log(item_id);
  console.log(file_id);
  fetch_post(`${API_URL}/delete-file-from-sample/`, {
    item_id: item_id,
    file_id: file_id,
  })
    .then(function (response_json) {
      store.commit("removeFileFromSample", {
        item_id: item_id,
        file_id: file_id,
      });
      store.commit("updateFiles", response_json.new_file_obj);
    })
    .catch((error) => alert(`Delete unsuccessful :(\n error: ${error}`));
}

export async function fetchRemoteTree(invalidate_cache) {
  var invalidate_cache_param = invalidate_cache ? "1" : "0";
  var url = new URL(
    `${API_URL}/list-remote-directories/?invalidate_cache=${invalidate_cache_param}`
  );
  console.log("fetchRemoteTree called!");
  store.commit("setRemoteDirectoryTreeIsLoading", true);
  return fetch_get(url)
    .then(function (response_json) {
      store.commit("setRemoteDirectoryTree", response_json);
      store.commit("setRemoteDirectoryTreeIsLoading", false);
      return response_json;
    })
    .catch((error) => {
      console.error("Error when fetching cached remote tree");
      console.error(error);
      store.commit("setRemoteDirectoryTreeIsLoading", false);
      throw error;
    });
}

export async function addRemoteFileToSample(file_entry, item_id) {
  console.log("loadSelectedRemoteFiles");
  return fetch_post(`${API_URL}/add-remote-file-to-sample/`, {
    file_entry: file_entry,
    item_id: item_id,
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
          item_id: item_id,
          file_id: response_json.file_id,
        });
      }
    })
    .catch((error) => `addRemoteFilesToSample unsuccessful. Error: ${error}`);
}

export async function getItemGraph() {
  return fetch_get(`${API_URL}/item-graph/`)
    .then(function (response_json) {
      console.log("received graph");
      store.commit("setItemGraph", { nodes: response_json.nodes, edges: response_json.edges });
    })
    .catch((error) => `getItemGraph unsuccessful. Error: ${error}`);
}

// export async function addRemoteFilesToSample(file_entries, item_id) {
//  console.log('loadSelectedRemoteFiles')
//  return fetch_post(`${API_URL}/add-remote-files-to-sample/`, {
//    file_entries: file_entries,
//    item_id: item_id,
//  }).then( function(response_json) {
//    //handle response
//    console.log("received remote samples!")
//    console.log(response_json)
//  }).catch( error => (`addRemoteFilesToSample unsuccessful. Error: ${error}`))
// }
