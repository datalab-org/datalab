// utility functions to deal with fetch calls to datalab gateway servers
// all code using fetch should be collected into this file

// import store from "@/store/index.js";
import { GATEWAY_URL } from "@/resources.js";

import { fetch_post } from "@/server_fetch_utils.js";

export function printQRCode(item_id, name, url, hcodes) {
  return fetch_post(`${GATEWAY_URL}/print-label/`, {
    item_id: item_id,
    name: name,
    url: url,
    hcodes: hcodes,
  });
}
