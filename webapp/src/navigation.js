import { findIconDefinition } from "@fortawesome/fontawesome-svg-core";
import { CONFIG } from "@/config.js";

// `isAvailable` is optional, but when defined it must be a predicate function.
// It receives `serverInfo` but predicates may ignore it, as Collections does.
export const NAVIGATION_VIEWS = {
  about: {
    routeName: "About",
    defaultLabel: "About",
  },
  samples: {
    routeName: "samples",
    defaultLabel: "Samples",
  },
  collections: {
    routeName: "collections",
    defaultLabel: "Collections",
    isAvailable: () => !CONFIG.HIDE_COLLECTIONS,
  },
  "starting-materials": {
    routeName: "starting-materials",
    defaultLabel: "Inventory",
  },
  equipment: {
    routeName: "equipment",
    defaultLabel: "Equipment",
  },
  "item-graph": {
    routeName: "item-graph",
    defaultLabel: "Graph View",
  },
};

// Compatibility fallback for API versions that predate `/info.navigation`.
// This can happen when a newer frontend connects to an older backend.
// Keep this list frozen at the original six-link navbar;
// current navigation defaults belong to the backend configuration.
const LEGACY_NAVIGATION = Object.freeze([
  { view: "about" },
  { view: "samples", default: true },
  { view: "collections" },
  { view: "starting-materials" },
  { view: "equipment" },
  { view: "item-graph", icon: "project-diagram" },
]);

function resolveIcon(icon, view) {
  if (!icon) return null;
  if (findIconDefinition({ prefix: "fas", iconName: icon })) return icon;

  console.warn(`Ignoring unregistered navigation icon ${JSON.stringify(icon)} for view ${view}.`);
  return null;
}

export function resolveNavigation(serverInfo) {
  if (serverInfo === null || serverInfo === undefined) return [];

  const navigation = Array.isArray(serverInfo.navigation)
    ? serverInfo.navigation
    : LEGACY_NAVIGATION;
  const knownViews = Object.keys(NAVIGATION_VIEWS);

  return navigation.flatMap((entry) => {
    const view = entry?.view;
    if (!knownViews.includes(view)) {
      console.warn(`Ignoring unknown navigation view ${JSON.stringify(view)}.`);
      return [];
    }
    const definition = NAVIGATION_VIEWS[view];
    // Conditional views use their catalog predicate to decide whether they are currently available.
    if (definition.isAvailable && !definition.isAvailable(serverInfo)) {
      console.warn(`Ignoring unavailable navigation view ${JSON.stringify(view)}.`);
      return [];
    }

    return [
      {
        view,
        routeName: definition.routeName,
        label: entry.label || definition.defaultLabel,
        icon: resolveIcon(entry.icon, view),
        default: entry.default,
      },
    ];
  });
}

export function resolveDefaultRouteName(serverInfo) {
  const navigation = resolveNavigation(serverInfo);
  const defaultEntry = navigation.find((entry) => entry.default);

  return defaultEntry?.routeName || navigation[0]?.routeName || NAVIGATION_VIEWS.samples.routeName;
}
