import "@uppy/core/dist/style.css";
import "@uppy/dashboard/dist/style.css";
import Uppy from "@uppy/core";
import Dashboard from "@uppy/dashboard";
import XHRUpload from "@uppy/xhr-upload";
import Webcam from "@uppy/webcam";

import store from "@/store/index.js";
import { construct_headers } from "@/server_fetch_utils.js";

import { API_URL, UPPY_MAX_NUMBER_OF_FILES, UPPY_MAX_TOTAL_FILE_SIZE } from "@/resources.js";
// file-upload loaded

export default function setupUppy(item_id, trigger_selector, reactive_file_list) {
  var uppy = new Uppy({
    restrictions: {
      // Somewhat arbitrary restrictions that prevent numbers that would break the server in one go -- the API should also refuse files when 'full'
      maxTotalFileSize: UPPY_MAX_TOTAL_FILE_SIZE, // Set this UI restriction arbitrarily high at 100 GB for now --- this is the point at which I would be unsure if the upload could even complete
      maxNumberOfFiles: UPPY_MAX_NUMBER_OF_FILES, // Similarly, a max of 10000 files in one upload as a single "File" entry feels reasonable, once we move to uploading folders etc.
    },
  });
  let headers = construct_headers();
  uppy
    .use(Dashboard, {
      inline: false,
      trigger: trigger_selector,
      close_after_finish: true,
    })
    .use(Webcam, { target: Dashboard })
    .use(XHRUpload, {
      //someday, try to upgrade this to Tus for resumable uploads
      headers: headers,
      endpoint: `${API_URL}/upload-file/`,
      FormData: true, // send as form
      fieldName: "files[]", // default, think about whether or not to change this
      showProgressDetails: true,
      withCredentials: true,
    });

  uppy.on("file-added", (file) => {
    var matching_file_id = null;
    for (const file_id in reactive_file_list) {
      if (reactive_file_list[file_id].name == file.name) {
        alert(
          "A file with this name already exists in the sample. If you upload this, it will be duplicated on the current item.",
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
    result.successful.forEach(function (f) {
      var response_body = f.response.body;
      if (!response_body.is_update) {
        store.commit("addFileToSample", {
          item_id: item_id,
          file_id: response_body.file_id,
          file_info: {
            ...response_body.file_information,
            immutable_id: response_body.file_information.immutable_id.$oid,
          },
        });
      }
    });
  });
}
