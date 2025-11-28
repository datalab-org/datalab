// utility functions to deal with fetch server calls
// all code using fetch should be collected into this file

import store from "@/store/index.js";
import {
  API_URL,
  API_TOKEN,
  SAMPLE_TABLE_TYPES,
  INVENTORY_TABLE_TYPES,
  EQUIPMENT_TABLE_TYPES,
} from "@/resources.js";

import { DialogService } from "@/services/DialogService";

/**
 * Waits for user info to finish loading and checks if user is authenticated.
 *
 *   if (!(await waitForUserAuth())) return;
 *
 * @returns {Promise<boolean>} Returns true if user is logged in, false otherwise
 */
async function waitForUserAuth() {
  if (store.state.currentUserInfoLoading) {
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        unwatch();
        reject(new Error("Timeout waiting for user info"));
      }, 10000); // 10 second timeout

      const unwatch = store.watch(
        (state) => state.currentUserInfoLoading,
        (newValue) => {
          if (!newValue) {
            clearTimeout(timeout);
            unwatch();
            resolve();
          }
        },
        { immediate: true },
      );
    }).catch(() => {
      DialogService.error({
        title: `Authentication Error`,
        message: "Encountered unexpected error when retrieving user credentials from API",
      });
    });
  }

  return store.getters.getCurrentUserID != null;
}

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
  return fetch(url, requestOptions).then(handleJSONResponse);
}

function fetch_post(url, body) {
  let headers = construct_headers({ "Content-Type": "application/json" });
  const requestOptions = {
    method: "POST",
    headers: headers,
    body: JSON.stringify(body),
    credentials: "include",
  };
  return fetch(url, requestOptions).then(handleJSONResponse);
}

function fetch_patch(url, body) {
  let headers = construct_headers({ "Content-Type": "application/json" });
  const requestOptions = {
    method: "PATCH",
    headers: headers,
    body: JSON.stringify(body),
    credentials: "include",
  };
  return fetch(url, requestOptions).then(handleJSONResponse);
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
  return fetch(url, requestOptions).then(handleJSONResponse);
}

// eslint-disable-next-line no-unused-vars
function fetch_delete(url, body) {
  let headers = construct_headers({ "Content-Type": "application/json" });
  const requestOptions = {
    method: "DELETE",
    headers: headers,
    body: JSON.stringify(body),
    credentials: "include",
  };
  return fetch(url, requestOptions).then(handleJSONResponse);
}

/**
 * Fetches a file with optional size limit checking
 * @param {string} url - The URL to fetch
 * @param {number} maxSizeBytes - Maximum allowed file size in bytes (default: 100 MB)
 * @returns {Promise<Response>} The fetch Response object
 * @throws {Error} If file exceeds size limit or fetch fails
 */
export async function fetch_file(url, maxSizeBytes = 100 * 1024 * 1024) {
  const requestOptions = {
    method: "GET",
    headers: construct_headers(),
    credentials: "include",
  };

  const response = await fetch(url, requestOptions);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  // Check Content-Length header if available to warn about large files
  // Note: This doesn't prevent the download (already happened), but provides
  // a better error message than running out of memory during response parsing
  const contentLength = response.headers.get("content-length");
  if (contentLength && parseInt(contentLength, 10) > maxSizeBytes) {
    throw new Error(
      `File too large: ${(parseInt(contentLength, 10) / 1024 / 1024).toFixed(2)} MB (max: ${(
        maxSizeBytes /
        1024 /
        1024
      ).toFixed(2)} MB)`,
    );
  }

  return response;
}

function handleJSONResponse(response) {
  return response.text().then((text) => {
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

export function createNewItem(
  item_id,
  type,
  date,
  name,
  startingCollection = null,
  startingData = {},
  copyFrom = null,
  generateIDAutomatically = false,
) {
  return fetch_post(`${API_URL}/new-sample/`, {
    copy_from_item_id: copyFrom,
    generate_id_automatically: generateIDAutomatically,
    new_sample_data: {
      item_id: item_id,
      date: date,
      name: name,
      type: type,
      collections: startingCollection,
      ...startingData,
    },
  }).then(function (response_json) {
    if (SAMPLE_TABLE_TYPES.includes(response_json.sample_list_entry.type)) {
      store.commit("prependToSampleList", response_json.sample_list_entry);
      if (startingCollection && startingCollection.length > 0) {
        getSampleList();
      }
    }
    if (INVENTORY_TABLE_TYPES.includes(response_json.sample_list_entry.type)) {
      store.commit("prependToStartingMaterialList", response_json.sample_list_entry);
      if (startingCollection && startingCollection.length > 0) {
        getStartingMaterialList();
      }
    }
    if (EQUIPMENT_TABLE_TYPES.includes(response_json.sample_list_entry.type)) {
      store.commit("prependToEquipmentList", response_json.sample_list_entry);
      if (startingCollection && startingCollection.length > 0) {
        getEquipmentList();
      }
    }
    return "success";
  });
}

export function createNewSamples(
  newSampleDatas,
  copyFromItemIds = null,
  generateIDsAutomatically = false,
) {
  return fetch_post(`${API_URL}/new-samples/`, {
    copy_from_item_ids: copyFromItemIds,
    new_sample_datas: newSampleDatas,
    generate_ids_automatically: generateIDsAutomatically,
  }).then(function (response_json) {
    response_json.responses.forEach((response) => {
      if (response.status == "success") {
        store.commit("prependToSampleList", response.sample_list_entry);
      }
    });

    return response_json.responses;
  });
}

export function createNewCollection(collection_id, title = "", startingData = {}, copyFrom = null) {
  return fetch_put(`${API_URL}/collections`, {
    copy_from_collection_id: copyFrom,
    data: {
      collection_id: collection_id,
      title: title,
      type: "collections",
      ...startingData,
    },
  }).then(function (response_json) {
    store.commit("prependToCollectionList", response_json.data);
    return "success";
  });
}

export async function getStats() {
  return fetch_get(`${API_URL}/info/stats`)
    .then(function (response_json) {
      return response_json.counts;
    })
    .catch((error) => {
      throw error;
    });
}

export async function getInfo() {
  return fetch_get(`${API_URL}/info`)
    .then(function (response_json) {
      store.commit("setServerInfo", response_json.data.attributes);
      return response_json.data.attributes;
    })
    .catch((error) => {
      DialogService.error({
        title: "Unable to retrieve API",
        message: `Unable to connect to the datalab instance at ${API_URL}.`,
      });
      throw error;
    });
}

export function getSampleList() {
  return fetch_get(`${API_URL}/samples/`)
    .then(function (response_json) {
      store.commit("setSampleList", response_json.samples);
    })
    .catch((error) => {
      if (error === "UNAUTHORIZED") {
        store.commit("setSampleList", []);
      } else {
        throw error;
      }
    });
}

export function getCollectionSampleList(collection_id) {
  return fetch_get(`${API_URL}/collections/${collection_id}`)
    .then(function (response_json) {
      store.commit("setCollectionSampleList", response_json);
    })
    .catch((error) => {
      if (error === "UNAUTHORIZED") {
        store.commit("setCollectionSampleList", []);
      } else {
        throw error;
      }
    });
}

export function getCollectionList() {
  return fetch_get(`${API_URL}/collections`)
    .then(function (response_json) {
      store.commit("setCollectionList", response_json.data);
    })
    .catch((error) => {
      if (error === "UNAUTHORIZED") {
        store.commit("setCollectionList", []);
      } else {
        throw error;
      }
    });
}

export function getUsersList() {
  return fetch_get(`${API_URL}/users`)
    .then(function (response_json) {
      const users = response_json.data;
      const hasUnverified = users.some((user) => user.account_status === "unverified");
      store.commit("updateHasUnverified", hasUnverified);

      return response_json.data;
    })
    .catch((error) => {
      throw error;
    });
}

export function getStartingMaterialList() {
  return fetch_get(`${API_URL}/starting-materials/`)
    .then(function (response_json) {
      store.commit("setStartingMaterialList", response_json.items);
    })
    .catch((error) => {
      if (error === "UNAUTHORIZED") {
        store.commit("setStartingMaterialList", []);
      } else {
        throw error;
      }
    });
}

export function getEquipmentList() {
  return fetch_get(`${API_URL}/equipment/`)
    .then(function (response_json) {
      store.commit("setEquipmentList", response_json.items);
    })
    .catch((error) => {
      if (error === "UNAUTHORIZED") {
        store.commit("setEquipmentList", []);
      } else {
        throw error;
      }
    });
}

export function searchItems(query, nresults = 100, types = null) {
  // construct a url with parameters:
  var url = new URL(`${API_URL}/search-items/`);
  var params = { query: query, nresults: nresults, types: types };
  Object.keys(params).forEach((key) => url.searchParams.append(key, params[key]));
  return fetch_get(url).then(function (response_json) {
    return response_json.items;
  });
}

export function searchCollections(query, nresults = 100) {
  // construct a url with parameters:
  var url = new URL(`${API_URL}/search-collections`);
  var params = { query: query, nresults: nresults };
  Object.keys(params).forEach((key) => url.searchParams.append(key, params[key]));
  return fetch_get(url).then(function (response_json) {
    return response_json.data;
  });
}

export async function getUserInfo() {
  store.commit("setCurrentUserInfoLoading", true);
  return fetch_get(`${API_URL}/get-current-user/`)
    .then((response_json) => {
      store.commit("setDisplayName", response_json.display_name);
      store.commit("setCurrentUserID", response_json.immutable_id);
      store.commit("setIsUnverified", response_json.account_status == "unverified" ? true : false);
      store.commit("setCurrentUserInfoLoading", false);
      return response_json;
    })
    .catch(() => {
      // If the user is not logged in, we return null.
      store.commit("setCurrentUserInfoLoading", false);
      return null;
    });
}

export async function requestMagicLink(email_address) {
  return fetch_post(`${API_URL}/login/magic-link`, {
    email: email_address,
    referrer: window.location.origin,
  })
    .then((response_json) => {
      return response_json;
    })
    .catch((err) => {
      DialogService.error({
        title: "Magic link request failed",
        message: `Failed to request magic link: ${err}`,
      });
      return err;
    });
}

export function searchUsers(query, nresults = 100) {
  // construct a url with parameters:
  var url = new URL(`${API_URL}/search-users/`);
  var params = { query: query, nresults: nresults };
  Object.keys(params).forEach((key) => url.searchParams.append(key, params[key]));
  return fetch_get(url).then(function (response_json) {
    return response_json.users;
  });
}

export function deleteSample(item_id) {
  return fetch_post(`${API_URL}/delete-sample/`, {
    item_id: item_id,
  })
    .then(function (response_json) {
      if (response_json.status !== "success") {
        throw new Error("Failed to delete sample: " + response_json.message);
      }
      store.commit("deleteFromSampleList", item_id);
    })
    .catch((error) => {
      DialogService.error({
        title: "Permission error",
        message:
          "Unable to delete item with ID '" +
          item_id +
          "': check that you have the appropriate permissions.",
      });
      throw error;
    });
}

export function deleteStartingMaterial(item_id) {
  return fetch_post(`${API_URL}/delete-sample/`, {
    item_id: item_id,
  })
    .then(function (response_json) {
      if (response_json.status !== "success") {
        throw new Error("Failed to delete starting material: " + response_json.message);
      }
      store.commit("deleteFromStartingMaterialList", item_id);
    })
    .catch((error) => {
      DialogService.error({
        title: "Permission error",
        message:
          "Unable to delete item with ID '" +
          item_id +
          "': check that you have the appropriate permissions.",
      });
      throw error;
    });
}

export function deleteCollection(collection_id, collection_summary) {
  return fetch_delete(`${API_URL}/collections/${collection_id}`)
    .then(function (response_json) {
      if (response_json.status !== "success") {
        throw new Error("Failed to delete collection: " + response_json.message);
      }
      store.commit("deleteFromCollectionList", collection_summary);
    })
    .catch((error) => {
      DialogService.error({
        title: "Permission error",
        message:
          "Unable to delete collection with ID '" +
          collection_id +
          "': check that you have the appropriate permissions.",
      });
      throw error;
    });
}

export function deleteEquipment(item_id) {
  return fetch_post(`${API_URL}/delete-sample/`, {
    item_id: item_id,
  })
    .then(function (response_json) {
      if (response_json.status !== "success") {
        throw new Error("Failed to delete equipment: " + response_json.message);
      }
      store.commit("deleteFromEquipmentList", item_id);
    })
    .catch((error) => {
      DialogService.error({
        title: "Permission error",
        message:
          "Unable to delete item with ID '" +
          item_id +
          "': check that you have the appropriate permissions.",
      });
      throw error;
    });
}

export function removeItemsFromCollection(collection_id, refcodes) {
  return fetch_delete(`${API_URL}/collections/${collection_id}/items`, {
    refcodes: refcodes,
  })
    .then(function (response_json) {
      store.commit("removeItemsFromCollection", {
        collection_id: collection_id,
        refcodes: refcodes,
      });

      return response_json;
    })
    .catch((error) => {
      DialogService.error({
        title: "Unable to remove item(s) from collection",
        message: "Collection delete failed for " + collection_id + ": " + error,
      });
    });
}

export async function getItemData(item_id, accessToken = null) {
  let url = `${API_URL}/get-item-data/${item_id}`;
  if (accessToken) {
    url += `?at=${accessToken}`;
  }

  return fetch_get(url)
    .then((response_json) => {
      store.commit("createItemData", {
        item_id: item_id,
        item_data: response_json.item_data,
        child_items: response_json.child_items,
        parent_items: response_json.parent_items,
      });
      return "success";
    })
    .catch((error) => {
      DialogService.error({
        title: "Unable to retrieve item",
        message: "Error getting item data: " + error,
      });
      throw error;
    });
}

export async function getItemByRefcode(refcode, accessToken = null) {
  let url = `${API_URL}/items/${refcode}`;
  if (accessToken) {
    url += `?at=${accessToken}`;
  }

  return fetch_get(url)
    .then((response_json) => {
      store.commit("createItemData", {
        refcode: refcode,
        item_id: response_json.item_data.item_id,
        item_data: response_json.item_data,
        child_items: response_json.child_items,
        parent_items: response_json.parent_items,
      });
      return "success";
    })
    .catch((error) => {
      DialogService.error({
        title: "Unable to retrieve item",
        message: "Error getting item data: " + error,
      });
      throw error;
    });
}

export async function getCollectionData(collection_id) {
  return fetch_get(`${API_URL}/collections/${collection_id}`)
    .then((response_json) => {
      store.commit("setCollectionData", {
        collection_id: collection_id,
        data: response_json.data,
        child_items: response_json.child_items,
      });

      return "success";
    })
    .catch((error) => {
      DialogService.error({
        title: "Unable to retrieve collection",
        message: "Error getting collection data: " + error,
      });
    });
}

export async function updateBlockFromServer(item_id, block_id, block_data, event_data = null) {
  // Send the current block state to the API and receive an updated version
  // of the block in return, including any event data.
  //
  // - Will strip known "large data" keys, even if not formalised, e.g., bokeh_plot_data.
  //
  // Short-circuit and do not send request if user is not logged in
  if (!(await waitForUserAuth())) return;

  delete block_data.bokeh_plot_data;
  delete block_data.b64_encoded_image;
  delete block_data.computed;
  delete block_data.metadata;

  store.commit("setBlockUpdating", block_id);
  return fetch_post(`${API_URL}/update-block/`, {
    item_id: item_id,
    block_id: block_id,
    block_data: block_data,
    event_data: event_data,
  })
    .then(function (response_json) {
      store.commit("updateBlockData", {
        item_id: item_id,
        block_id: block_id,
        block_data: response_json.new_block_data,
      });
      store.commit("setBlockNotUpdating", block_id);
      store.commit("setBlockSaved", {
        block_id: block_id,
        isSaved: response_json.saved_successfully,
      });
      store.commit("setBlockError", { block_id, error: "" });
    })
    .catch((error) => {
      // The block component renders errors, so no need to make a dialog here.
      store.commit("setBlockNotUpdating", block_id);
      if (error && !error.includes("Invalid block type")) {
        // Do not set any error message for NotImplemented as this will be handled elsewhere
        store.commit("setBlockError", { block_id, error: error });
      }
    });
}

export function addABlock(item_id, block_type, index = null) {
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
    .catch((error) => {
      DialogService.error({
        title: "Failed to add block",
        message: `Error adding block to item ${item_id}: ${error}`,
      });
      throw error;
    });
  return block_id_promise;
}

export function updateItemPermissions(refcode, creators) {
  return fetch_patch(`${API_URL}/items/${refcode}/permissions`, {
    creators: creators,
  }).then(function (response_json) {
    if (response_json.status === "error") {
      DialogService.error({
        title: "Permission update failed",
        message: `Failed to update permissions for item ${refcode}: ${response_json.message}`,
      });
      throw new Error(response_json.message);
    }
    return response_json;
  });
}

export function saveItem(item_id) {
  var item_data = store.state.all_item_data[item_id];

  let blocks = [];
  let keysToExclude = ["bokeh_plot_data", "computed", "metadata", "b64_encoded_image"];

  // Strip large data from blocks before saving, but make
  // sure to preserve them in the store
  if (item_data.blocks_obj) {
    for (const block_id in item_data.blocks_obj) {
      blocks.push(
        Object.fromEntries(
          Object.entries(item_data.blocks_obj[block_id]).filter(
            ([key]) => !keysToExclude.includes(key),
          ),
        ),
      );
    }
  }

  item_data.blocks = blocks;

  store.commit("setItemSaved", { item_id: item_id, isSaved: false });
  fetch_post(`${API_URL}/save-item/`, {
    item_id: item_id,
    data: item_data,
  })
    .then(function (response_json) {
      if (response_json.status === "success") {
        store.commit("updateItemData", {
          item_id: item_id,
          item_data: { last_modified: response_json.last_modified },
        });
        store.commit("setItemSaved", { item_id: item_id, isSaved: true });
        store.state.all_item_data[item_id].display_order.forEach((block_id) => {
          store.commit("setBlockSaved", { block_id: block_id, isSaved: true });
        });
      }
    })
    .catch(function (error) {
      DialogService.error({
        title: "Failed to save item",
        message: "Save unsuccessful: " + error,
      });
    });
}

export function saveCollection(collection_id) {
  var data = store.state.all_collection_data[collection_id];
  fetch_patch(`${API_URL}/collections/${collection_id}`, { data: data })
    .then(function (response_json) {
      if (response_json.status === "success") {
        store.commit("setSavedCollection", { collection_id: collection_id, isSaved: true });
      }
    })
    .catch(function (error) {
      DialogService.error({
        title: "Failed to save collection",
        message: "Save unsuccessful: " + error,
      });
    });
}

export function saveUser(user_id, user) {
  fetch_patch(`${API_URL}/users/${user_id}`, user)
    .then(function (response_json) {
      if (response_json.status === "success") {
        getUserInfo();
      } else {
        DialogService.error({
          title: "Failed to update user",
          message: "User save unsuccessful: " + response_json.detail,
        });
      }
    })
    .catch(function (error) {
      DialogService.error({
        title: "Failed to update user",
        message: `User save unsuccessful: ${error}`,
      });
    });
}

export function saveRole(user_id, role) {
  fetch_patch(`${API_URL}/roles/${user_id}`, role)
    .then(function (response_json) {
      if (response_json.status !== "success") {
        throw new Error("Failed to save role: " + response_json.detail);
      }
    })
    .catch(function (error) {
      DialogService.error({
        title: "Role save failed",
        message: `Role save unsuccessful: ${error}`,
      });
    });
}

export function deleteBlock(item_id, block_id) {
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
    .catch((error) => {
      DialogService.error({
        title: "Block deletion failed",
        message: `Delete unsuccessful: ${error}`,
      });
    });
}

export function deleteFileFromSample(item_id, file_id) {
  fetch_post(`${API_URL}/delete-file-from-sample/`, {
    item_id: item_id,
    file_id: file_id,
  })
    .then(function () {
      store.commit("removeFileFromSample", {
        item_id: item_id,
        file_id: file_id,
      });
    })
    .catch((error) => {
      DialogService.error({
        title: "Failed to unlink file",
        message: `Delete unsuccessful: ${error}`,
      });
    });
}

export async function fetchRemoteTree(invalidate_cache) {
  if (!(await waitForUserAuth())) return;

  var invalidate_cache_param = invalidate_cache ? "1" : "0";
  var url = new URL(
    `${API_URL}/list-remote-directories?invalidate_cache=${invalidate_cache_param}`,
  );
  store.commit("setRemoteDirectoryTreeIsLoading", true);
  return fetch_get(url)
    .then(function (response_json) {
      store.commit("setRemoteDirectoryTree", response_json);
      store.commit("setRemoteDirectoryTreeIsLoading", false);
      return response_json;
    })
    .catch((error) => {
      DialogService.error({
        title: "Remote directory retrieval failed",
        message: `Error retrieving remote directory tree from API: ${error}`,
      });
      store.commit("setRemoteDirectoryTreeIsLoading", false);
      throw error;
    });
}

export async function addRemoteFileToSample(file_entry, item_id) {
  return fetch_post(`${API_URL}/add-remote-file-to-sample/`, {
    file_entry: file_entry,
    item_id: item_id,
  })
    .then(function (response_json) {
      if (!response_json.is_update) {
        store.commit("addFileToSample", {
          item_id: item_id,
          file_id: response_json.file_id,
          file_info: response_json.file_information,
        });
      }
    })
    .catch((error) =>
      DialogService.error({
        title: "Remote File Linking Failed",
        message: `Error adding remote file to sample: ${error}`,
      }),
    );
}

export async function getItemGraph({ item_id = null, collection_id = null } = {}) {
  // Short-circuit and do not send request if user is not logged in
  if (!(await waitForUserAuth())) return;

  let url = `${API_URL}/item-graph`;
  if (item_id != null) {
    url = url + "/" + item_id;
  }
  if (collection_id != null) {
    url = url + "?collection_id=" + collection_id;
  }

  const urlParams = new URLSearchParams(window.location.search);
  const accessToken = urlParams.get("at");

  store.commit("setItemGraphIsLoading", true);
  return fetch_get(url)
    .then(function (response_json) {
      store.commit("setItemGraph", { nodes: response_json.nodes, edges: response_json.edges });
      store.commit("setItemGraphIsLoading", false);
    })
    .catch((error) => {
      store.commit("setItemGraphIsLoading", false);
      if (!accessToken) {
        DialogService.error({
          title: "Graph Retrieval Failed",
          message: `Error retrieving item graph from API: ${error}`,
        });
      }
    });
}

export async function requestNewAPIKey() {
  try {
    const response_json = await fetch_get(`${API_URL}/get-api-key/`);

    if (response_json.key) {
      return response_json.key;
    } else {
      DialogService.error({
        title: "API Key Request Failed",
        message: "Failed to retrieve new API key. Please try again later or report this issue.",
      });
      throw new Error(response_json.message);
    }
  } catch (error) {
    DialogService.error({
      title: "API Key Request Failed",
      message: "Failed to retrieve new API key. Please try again later or report this issue.",
    });
    throw new Error(`Failed to request new API key: ${error.message}`);
  }
}

export async function getBlocksInfos() {
  return fetch_get(`${API_URL}/info/blocks`)
    .then(function (response_json) {
      store.commit("setBlocksInfos", response_json.data);
      return response_json.data;
    })
    .catch((error) => {
      DialogService.error({
        title: "Block Info Retrieval Failed",
        message: `Error retrieving block infos from API: ${error}`,
      });
      throw error;
    });
}

export function addItemsToCollection(collection_id, refcodes) {
  return fetch_post(`${API_URL}/collections/${collection_id}`, {
    data: { refcodes },
  })
    .then(function (response_json) {
      if (response_json.status === "success") {
        return response_json;
      } else {
        throw new Error("Failed to add items to collection.");
      }
    })
    .catch(function (error) {
      DialogService.error({
        title: "Collection Update Failed",
        message: "Error adding items to collection: " + error,
      });
      throw error;
    });
}

export async function getSupportedSchemasList() {
  return fetch_get(`${API_URL}/info/types`)
    .then(function (response_json) {
      if (response_json) {
        return response_json.data;
      } else {
        throw new Error("Failed to get schemas from API.");
      }
    })
    .catch(function (error) {
      DialogService.error({
        title: "Schema Retrieval Failed",
        message: `Error retrieving schemas from API: ${error}`,
      });
      throw error;
    });
}

export async function getSchema(type) {
  return fetch_get(`${API_URL}/info/types/${type}`)
    .then(function (response_json) {
      if (response_json) {
        return response_json.data;
      } else {
        throw new Error(`Failed to get ${type} schemas from API.`);
      }
    })
    .catch(function (error) {
      DialogService.error({
        title: "Schema Retrieval Failed",
        message: `Error retrieving ${type} schema from API: ${error}`,
      });
      throw error;
    });
}
