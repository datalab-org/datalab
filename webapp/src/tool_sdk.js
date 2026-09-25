import * as Vue from "vue";

import BokehPlot from "@/components/BokehPlot.vue";
import ChemicalFormula from "@/components/ChemicalFormula.vue";
import FormattedItemName from "@/components/FormattedItemName.vue";
import ItemSelect from "@/components/ItemSelect.vue";
import { API_URL } from "@/resources.js";
import { DialogService } from "@/services/DialogService.js";
import { toolApiGet, toolApiPost } from "@/server_fetch_utils.js";

export const TOOL_SDK_VERSION = 1;

const MAX_SELECTED_ITEM_REFCODES = 100;
const registeredInAppTools = new Map();
const inAppToolLoads = new Map();
const expectedRegistrations = new Set();
let publicSdk = null;

function normalizeQueryValues(value, limit = Number.POSITIVE_INFINITY) {
  const values = Array.isArray(value) ? value : value == null ? [] : [value];
  const normalized = [];
  const seen = new Set();
  for (const candidate of values) {
    if (typeof candidate !== "string") {
      continue;
    }
    const value = candidate.trim();
    if (value && !seen.has(value)) {
      seen.add(value);
      normalized.push(value);
      if (normalized.length === limit) {
        break;
      }
    }
  }
  return normalized;
}

function registerInAppTool(component) {
  const id = document.currentScript?.dataset?.datalabToolId;
  if ((typeof component !== "object" || component === null) && typeof component !== "function") {
    throw new Error("An in-app tool must register a frontend component.");
  }
  if (!id || !expectedRegistrations.has(id)) {
    throw new Error("This in-app tool was not requested by the datalab tool host.");
  }
  if (registeredInAppTools.has(id)) {
    throw new Error(`In-app tool ${id} is already registered.`);
  }

  registeredInAppTools.set(id, component);
}

function providerBaseUrl(toolId) {
  const apiBase = new URL(`${API_URL.replace(/\/+$/, "")}/`, window.location.origin);
  return new URL(`tools/plugins/${encodeURIComponent(toolId)}/`, apiBase);
}

function resolveEntrypointUrl(tool) {
  const entrypoint = tool?.ui?.entrypoint;
  if (typeof entrypoint !== "string" || entrypoint.length === 0) {
    throw new Error(`In-app tool ${tool?.id || ""} has no frontend entrypoint.`);
  }

  const baseUrl = providerBaseUrl(tool.id);
  const entrypointUrl = new URL(entrypoint, baseUrl);
  if (
    entrypointUrl.origin !== baseUrl.origin ||
    !entrypointUrl.pathname.startsWith(baseUrl.pathname)
  ) {
    throw new Error(`In-app tool ${tool.id} has an unsafe frontend entrypoint.`);
  }
  return entrypointUrl.href;
}

function loadInAppToolScript(tool) {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    let settled = false;
    const finish = (callback, value, removeScript = false) => {
      if (settled) {
        return;
      }
      settled = true;
      window.clearTimeout(timeout);
      expectedRegistrations.delete(tool.id);
      if (removeScript) {
        script.remove();
      }
      callback(value);
    };

    script.async = true;
    script.crossOrigin = "use-credentials";
    script.dataset.datalabToolId = tool.id;
    script.src = resolveEntrypointUrl(tool);
    expectedRegistrations.add(tool.id);
    script.addEventListener("load", () => {
      const component = registeredInAppTools.get(tool.id);
      if (!component) {
        finish(
          reject,
          new Error(`In-app tool ${tool.id} loaded without registering a component.`),
          true,
        );
        return;
      }
      finish(resolve, component);
    });
    script.addEventListener("error", () => {
      finish(
        reject,
        new Error(`Unable to load the frontend bundle for ${tool.name || tool.id}.`),
        true,
      );
    });
    const timeout = window.setTimeout(() => {
      finish(
        reject,
        new Error(`Timed out while loading the frontend bundle for ${tool.name || tool.id}.`),
        true,
      );
    }, 15000);
    document.head.appendChild(script);
  });
}

export async function loadInAppTool(tool) {
  const component = registeredInAppTools.get(tool.id);
  if (component) {
    return component;
  }

  if (!inAppToolLoads.has(tool.id)) {
    const load = loadInAppToolScript(tool).catch((error) => {
      inAppToolLoads.delete(tool.id);
      throw error;
    });
    inAppToolLoads.set(tool.id, load);
  }
  return inAppToolLoads.get(tool.id);
}

export function installToolSdk(router) {
  if (publicSdk) {
    return publicSdk;
  }

  const components = Object.freeze({
    BokehPlot,
    ChemicalFormula,
    FormattedItemName,
    ItemSelect,
  });
  const api = Object.freeze({
    baseUrl: API_URL,
    get: toolApiGet,
    post: toolApiPost,
  });
  const navigation = Object.freeze({
    currentRoute: () => router.currentRoute.value,
    push: (location) => router.push(location),
    replace: (location) => router.replace(location),
  });
  const selection = Object.freeze({
    current: () => {
      const query = router.currentRoute.value.query;
      const actionId = normalizeQueryValues(query.action, 1)[0] || null;
      return Object.freeze({
        actionId,
        itemRefcodes: Object.freeze(normalizeQueryValues(query.items, MAX_SELECTED_ITEM_REFCODES)),
      });
    },
    replaceItemRefcodes: (refcodes) => {
      const query = { ...router.currentRoute.value.query };
      const normalized = normalizeQueryValues(refcodes, MAX_SELECTED_ITEM_REFCODES);
      if (normalized.length) {
        query.items = normalized;
      } else {
        delete query.items;
      }
      return router.replace({ query });
    },
  });
  const dialogs = Object.freeze({
    alert: (options) => DialogService.alert(options),
    confirm: (options) => DialogService.confirm(options),
    error: (options) => DialogService.error(options),
  });

  publicSdk = Object.freeze({
    version: TOOL_SDK_VERSION,
    runtime: Vue,
    components,
    api,
    navigation,
    selection,
    dialogs,
    register: registerInAppTool,
  });

  if (
    Object.prototype.hasOwnProperty.call(window, "datalabToolSdk") &&
    window.datalabToolSdk !== publicSdk
  ) {
    throw new Error("The datalab tool SDK global is already defined.");
  }
  Object.defineProperty(window, "datalabToolSdk", {
    configurable: false,
    enumerable: false,
    writable: false,
    value: publicSdk,
  });
  return publicSdk;
}
