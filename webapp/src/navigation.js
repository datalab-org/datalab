import { findIconDefinition } from "@fortawesome/fontawesome-svg-core";

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

function resolveIcon(icon, view) {
  if (!icon) return null;
  if (findIconDefinition({ prefix: "fas", iconName: icon })) return icon;

  console.warn(`Ignoring unregistered navigation icon ${JSON.stringify(icon)} for view ${view}.`);
  return null;
}

export function resolveNavigation(serverInfo) {
  const navigation = Array.isArray(serverInfo?.navigation) ? serverInfo.navigation : [];

  return navigation.flatMap((entry) => {
    const view = entry?.view;
    const definition = NAVIGATION_VIEWS[view];
    if (!definition) {
      console.warn(`Ignoring unknown navigation view ${JSON.stringify(view)}.`);
      return [];
    }
    // Views can become conditional when their corresponding feature exists by adding, e.g.,
    // `isAvailable: (info) => info.features.collections_enabled` to their catalog entry.
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
      },
    ];
  });
}
