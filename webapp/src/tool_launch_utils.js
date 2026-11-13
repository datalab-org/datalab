import { launchTool } from "@/server_fetch_utils.js";
import { findIconDefinition } from "@fortawesome/fontawesome-svg-core";

const ITEM_TABLE_IDS = Object.freeze({
  samples: "samples",
  startingMaterials: "inventory",
  equipment: "equipment",
  collectionItems: "collection-items",
});

export function parseToolLaunchUrl(url) {
  const parsedUrl = new URL(url, window.location.origin);
  if (
    !["http:", "https:"].includes(parsedUrl.protocol) ||
    parsedUrl.username ||
    parsedUrl.password
  ) {
    throw new Error("The tool returned an unsafe launch URL.");
  }
  return parsedUrl.href;
}

export function openToolPlaceholderTab(url = "about:blank") {
  const launchWindow = window.open(url, "_blank");
  if (!launchWindow) {
    throw new Error(
      "The new tab was blocked by your browser. Allow pop-ups for this site and try again.",
    );
  }
  launchWindow.opener = null;
  return launchWindow;
}

export function toolIcon(tool) {
  const iconName = typeof tool?.icon === "string" ? tool.icon : "";
  return iconName && findIconDefinition({ prefix: "fas", iconName }) ? iconName : "laptop-code";
}

export function isSupportedTool(tool) {
  return (
    (tool?.ui?.kind === "standalone" && ["same_tab", "new_tab"].includes(tool.ui.open_mode)) ||
    (tool?.ui?.kind === "in_app" &&
      ["same_tab", "new_tab"].includes(tool.ui.open_mode) &&
      tool.ui.sdk_version === 1 &&
      typeof tool.ui.entrypoint === "string" &&
      tool.ui.entrypoint.length > 0)
  );
}

export function itemTableSelectionActions(tools, dataType) {
  const tableId = ITEM_TABLE_IDS[dataType];
  if (!tableId) {
    return [];
  }

  return tools.flatMap((tool) =>
    (tool.launch_actions || [])
      .filter(
        (action) =>
          action?.kind === "item-table-selection" &&
          Array.isArray(action.tables) &&
          action.tables.includes(tableId),
      )
      .map((action) => ({ action, tool })),
  );
}

export function normalizeStringValues(value, limit = Number.POSITIVE_INFINITY) {
  const values = Array.isArray(value) ? value : value == null ? [] : [value];
  const normalized = [];
  const seen = new Set();
  for (const candidate of values) {
    if (typeof candidate !== "string") {
      continue;
    }
    const trimmed = candidate.trim();
    if (trimmed && !seen.has(trimmed)) {
      seen.add(trimmed);
      normalized.push(trimmed);
      if (normalized.length === limit) {
        break;
      }
    }
  }
  return normalized;
}

export function selectionLaunchPayload(selection) {
  if (!selection) {
    return {};
  }
  return {
    action: selection.actionId,
    items: selection.itemRefcodes,
  };
}

export function selectionFromRouteQuery(query) {
  const action = normalizeStringValues(query?.action, 1)[0];
  const items = normalizeStringValues(query?.items, 100);
  if (action == null && items.length === 0) {
    return null;
  }
  return {
    actionId: action,
    itemRefcodes: items,
  };
}

export async function openTool(tool, router, selection = null) {
  if (!isSupportedTool(tool)) {
    throw new Error("This tool requires an unsupported frontend integration.");
  }

  if (tool.ui.kind === "in_app") {
    const query = selection
      ? {
          action: selection.actionId,
          items: selection.itemRefcodes,
        }
      : undefined;
    const route = { name: "tool", params: { toolId: tool.id }, query };
    if (tool.ui.open_mode === "same_tab") {
      await router.push(route);
      return;
    }

    const url = new URL(router.resolve(route).href, window.location.origin).href;
    openToolPlaceholderTab(url);
    return;
  }

  const launchWindow = tool.ui.open_mode === "new_tab" ? openToolPlaceholderTab() : null;
  try {
    const launch = await launchTool(tool.id, selectionLaunchPayload(selection));
    if (typeof launch.url !== "string") {
      throw new Error("The tool returned an unexpected launch result.");
    }
    const launchUrl = parseToolLaunchUrl(launch.url);
    if (launchWindow) {
      launchWindow.location.replace(launchUrl);
    } else {
      window.location.assign(launchUrl);
    }
  } catch (error) {
    launchWindow?.close();
    throw error;
  }
}

export async function openToolForItemSelection(tool, action, items, router) {
  if (!isSupportedTool(tool) || action?.kind !== "item-table-selection") {
    throw new Error("This tool does not support a table-selection action.");
  }

  const itemRefcodes = [...new Set(items.map((item) => item?.refcode))];
  if (itemRefcodes.some((refcode) => typeof refcode !== "string" || !refcode)) {
    throw new Error("Every selected item must have an immutable refcode.");
  }
  if (itemRefcodes.length < action.min_items || itemRefcodes.length > action.max_items) {
    throw new Error("The selected-item count is outside this tool action's limits.");
  }

  await openTool(tool, router, {
    actionId: action.id,
    itemRefcodes,
  });
}
