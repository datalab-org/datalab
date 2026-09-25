import { getTools } from "@/server_fetch_utils.js";

let cachedTools = null;
let pendingRequest = null;

export async function loadToolCatalog({ refresh = false } = {}) {
  if (!refresh && cachedTools !== null) {
    return cachedTools;
  }
  if (pendingRequest !== null) {
    return pendingRequest;
  }

  pendingRequest = getTools()
    .then((tools) => {
      cachedTools = tools;
      return tools;
    })
    .finally(() => {
      pendingRequest = null;
    });
  return pendingRequest;
}

export function clearToolCatalog() {
  cachedTools = null;
  pendingRequest = null;
}
