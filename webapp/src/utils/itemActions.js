/**
 * Actions that can be applied to rows of a `DynamicDataTable`, either to a single row (from
 * its row action buttons) or to the current selection (from the "Actions" menu).
 *
 * These are plain objects, meant to be treated as read-only, like the column definitions in
 * `tableColumns.js`. Controls only read them to decide what to show, then emit an action
 * request `{ action, items, source }` naming the action by its `key`; carrying out the action
 * is left to `ItemActionsHandler`.
 *
 * - `label`: the entry in the selection's "Actions" menu; `rowLabel`: the row button's tooltip.
 * - `dataTypes`: the tables offering the action on a selection.
 * - `rowDataTypes`: the tables offering it on a single row (defaults to `dataTypes`).
 */

export const ADD_TO_COLLECTION_ACTION = {
  key: "add-to-collection",
  label: "Add item(s) to collection",
  rowLabel: "Add to collection",
  icon: "folder-plus",
  dataTypes: ["samples", "startingMaterials", "equipment"],
};

export const SHARE_ACTION = {
  key: "share",
  label: "Share item(s)",
  rowLabel: "Share",
  icon: "share-alt",
  dataTypes: ["samples", "startingMaterials", "equipment"],
};

export const DELETE_ACTION = {
  key: "delete",
  label: "Delete item(s)",
  rowLabel: "Delete",
  icon: "trash",
  dataTypes: ["samples", "collections", "startingMaterials", "equipment", "tags"],
  // Tags already have their own per-row edit/delete buttons (`TagActionsCell`).
  rowDataTypes: ["samples", "collections", "startingMaterials", "equipment"],
};

export const ITEM_ACTIONS = [ADD_TO_COLLECTION_ACTION, SHARE_ACTION, DELETE_ACTION];

/** The actions offered on a selection of rows in the given table. */
export function batchActionsFor(dataType) {
  return ITEM_ACTIONS.filter((action) => action.dataTypes.includes(dataType));
}

/** The actions offered on a single row of the given table. */
export function rowActionsFor(dataType) {
  return ITEM_ACTIONS.filter((action) =>
    (action.rowDataTypes || action.dataTypes).includes(dataType),
  );
}
