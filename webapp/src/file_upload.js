import "@uppy/core/dist/style.css";
import "@uppy/dashboard/dist/style.css";
import Uppy from "@uppy/core";
import Dashboard from "@uppy/dashboard";
import XHRUpload from "@uppy/xhr-upload";
import Webcam from "@uppy/webcam";

import store from "@/store/index.js";
import { construct_headers } from "@/server_fetch_utils.js";

import { API_URL } from "@/resources.js";
// file-upload loaded

export default function setupUppy(item_id, trigger_selector, reactive_file_list) {
  console.log("setupUppy called with: " + trigger_selector);
  var uppy = new Uppy();
  let headers = construct_headers();
  uppy
    .use(Dashboard, {
      inline: false,
      trigger: trigger_selector,
      close_after_finish: true,
      metaFields: [
        {
          id: "blahblah",
          name: "Blah",
          placeholder: "Metadata can be added here",
        },
      ],
    })
    .use(Webcam, { target: Dashboard })
    .use(XHRUpload, {
      //someday, try to upgrade this to Tus
      headers: headers,
      endpoint: `${API_URL}/upload-file/`,
      FormData: true, // send as form
      fieldName: "files[]", // default, think about whether or not to change this
      showProgressDetails: true,
      // getResponseData(responseText, response) {
      // 	console.log("Uppy response text:")
      // 	console.log(responseText)
      // 	console.log("Uppy response:")
      // 	console.log(response)
      // }
    });

  uppy.on("file-added", (file) => {
    console.log("searching for matching files for: " + file.name);
    var matching_file_id = null;
    for (const file_id in reactive_file_list) {
      // console.log(`evaluating ${reactive_file_list[file_id].name} vs ${file.name}`)
      if (reactive_file_list[file_id].name == file.name) {
        matching_file_id = file_id;
        alert(
          "A file with this name already exists in the sample. If you upload this, it will update the current file."
        );
      }
    }

    uppy.setFileMeta(file.id, {
      size: file.size,
      item_id: item_id,
      replace_file: matching_file_id,
    });
  });

  uppy.on("complete", function (result) {
    console.log("Upload complete! We’ve uploaded these files:", result.successful);
    console.log("There were errors with these files:", result.failed);
    result.successful.forEach(function (f) {
      console.log("file upload response:");
      console.log(f.response);
      var response_body = f.response.body;
      store.commit("updateFiles", {
        [response_body.file_id]: response_body.file_information,
      });
      console.log("Added file to store. Response_body:");
      console.log(response_body);
      if (!response_body.is_update) {
        store.commit("addFileToSample", {
          item_id: item_id,
          file_id: response_body.file_id,
        });
      }
    });
  });
}
