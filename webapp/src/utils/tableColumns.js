import { FilterOperator, FilterMatchMode } from "@primevue/core/api";

import { formatRelativeDate } from "@/field_utils.js";

import BlocksIconCounter from "@/components/BlocksIconCounter";
import ChemicalFormula from "@/components/ChemicalFormula";
import CollectionList from "@/components/CollectionList";
import Creators from "@/components/Creators";
import FilesIconCounter from "@/components/FilesIconCounter";
import FormattedCollectionName from "@/components/FormattedCollectionName";
import FormattedItemName from "@/components/FormattedItemName";
import FormattedItemStatus from "@/components/FormattedItemStatus";

import CreatorsAndGroupsFilter from "@/components/CreatorsAndGroupsFilter";
import DateRangeFilter from "@/components/DateRangeFilter";
import MultiSelectFilter from "@/components/MultiSelectFilter";
import TextFilter from "@/components/TextFilter";

import {
  matchByKey,
  keyedOptions,
  matchStatus,
  matchCollections,
  matchCreatorsAndGroups,
  matchBlocks,
  collectionsOptions,
  creatorsAndGroupsOptions,
  statusOptions,
  blocksOptions,
} from "@/utils/filterMatchers";

/**
 * Column definitions shared by the item tables (samples, starting materials, equipment and
 * a collection's children).
 *
 * These are plain objects, meant to be treated as read-only: a table that needs to differ
 * spreads the shared definition and overrides the keys it cares about, so the difference is
 * visible at the call site rather than hidden behind an argument. `DynamicDataTable` only
 * ever reads them.
 *
 * The `label` on each column is the name shown in the column-toggle menu, which falls back
 * to the header when absent.
 */

/**
 * The item's ID, rendered as a link to its edit page.
 *
 * Rows are expected to carry their own `type`. Tables listing a single kind of item override
 * `body.props` to supply a fallback type for rows that have none, which picks the icon and
 * colour.
 */
export const ITEM_ID_COLUMN = {
  field: "item_id",
  header: "ID",
  label: "ID",
  body: {
    component: FormattedItemName,
    props: (row) => ({
      item_id: row.item_id,
      itemType: row.type,
      enableClick: true,
      enableModifiedClick: true,
    }),
  },
  filter: {
    component: TextFilter,
    componentProps: { placeholder: "Search by ID" },
    matchMode: FilterMatchMode.CONTAINS,
    operator: FilterOperator.AND,
  },
};

/** The item type, filterable against the types actually present in the table. */
export const TYPE_COLUMN = {
  field: "type",
  header: "Type",
  label: "Type",
  filter: {
    component: MultiSelectFilter,
    componentProps: { optionLabel: "type", placeholder: "Select item types" },
    match: matchByKey("type"),
    operator: FilterOperator.AND,
    options: keyedOptions("type"),
    noOperator: true,
  },
};

/** The item status, rendered as a coloured badge. */
export const STATUS_COLUMN = {
  field: "status",
  header: "Status",
  label: "Status",
  body: {
    component: FormattedItemStatus,
    props: (row) => ({ status: row.status }),
  },
  filter: {
    component: MultiSelectFilter,
    componentProps: {
      optionLabel: "status",
      placeholder: "Select status",
      optionComponent: FormattedItemStatus,
      optionProps: (opt) => ({ status: opt.status, dotOnly: false }),
      valueComponent: FormattedItemStatus,
      valueProps: (val) => ({ status: val.status, dotOnly: false }),
    },
    match: matchStatus,
    operator: FilterOperator.OR,
    options: statusOptions,
    noOperator: true,
  },
};

/** The item name, as plain text. */
export const NAME_COLUMN = { field: "name", header: "Name", label: "Name" };

/** The chemical formula, rendered with its associated structural information. */
export const CHEMFORM_COLUMN = {
  field: "chemform",
  header: "Formula",
  label: "Formula",
  body: {
    component: ChemicalFormula,
    props: (row) => ({
      formula: row.chemform,
      smiles: row.smiles,
      inchiKey: row.inchi_key,
      ghsCodes: row.GHS_codes,
      molarMass: row.molar_mass,
      cas: row.CAS,
    }),
  },
};

/** The creation date, truncated to the day. Unfiltered; see {@link DATE_RANGE_FILTER}. */
export const DATE_COLUMN = {
  field: "date",
  header: "Date",
  label: "Date",
  getValue: (row) => (row.date ? row.date.substring(0, 10) : row.date),
};

/** The range/before/after date filter, for tables that want a filterable date column. */
export const DATE_RANGE_FILTER = {
  component: DateRangeFilter,
  matchMode: "dateRange",
  operator: FilterOperator.AND,
  noOperator: true,
};

/** The collections the item belongs to. */
export const COLLECTIONS_COLUMN = {
  field: "collections",
  header: "Collections",
  label: "Collections",
  body: {
    component: CollectionList,
    props: (row) => ({ collections: row.collections }),
  },
  filter: {
    component: MultiSelectFilter,
    componentProps: {
      optionLabel: "collection_id",
      optionComponent: FormattedCollectionName,
      optionProps: (opt) => ({ collection_id: opt.collection_id, size: 24 }),
      valueComponent: FormattedCollectionName,
      valueProps: (val) => ({ collection_id: val.collection_id, size: 20 }),
    },
    match: matchCollections,
    operator: FilterOperator.AND,
    options: collectionsOptions,
  },
};

/**
 * The item's creators and groups, rendered as avatars.
 *
 * Rows are expected to carry a `creatorsAndGroups` array of creators and groups tagged with
 * a `type`; rows that predate it fall back to their separate `creators` and `groups` fields.
 */
export const CREATORS_AND_GROUPS_COLUMN = {
  field: "creatorsAndGroups",
  header: "Creators",
  label: "Creators",
  body: {
    component: Creators,
    props: (row) => ({
      creators: row.creatorsAndGroups
        ? row.creatorsAndGroups.filter((item) => item.type === "creator")
        : row.creators || [],
      groups: row.creatorsAndGroups
        ? row.creatorsAndGroups.filter((item) => item.type === "group")
        : row.groups || [],
      showNames:
        (row.creatorsAndGroups || row.creators || []).filter(
          (item) => !item.type || item.type === "creator",
        ).length === 1,
      showBubble: true,
    }),
  },
  filter: {
    component: CreatorsAndGroupsFilter,
    match: matchCreatorsAndGroups,
    operator: FilterOperator.AND,
    options: creatorsAndGroupsOptions,
  },
};

/** A count of the item's blocks, filterable by block type. */
export const BLOCKS_COLUMN = {
  field: "blocks",
  header: "",
  icon: ["fa", "cubes"],
  label: "Blocks",
  body: {
    component: BlocksIconCounter,
    props: (row) => ({ count: row.nblocks, blockInfo: row.blocks }),
  },
  filter: {
    component: MultiSelectFilter,
    componentProps: { optionLabel: "label", placeholder: "Select block types" },
    match: matchBlocks,
    operator: FilterOperator.AND,
    options: blocksOptions,
  },
};

/** A count of the files attached to the item. */
export const FILES_COLUMN = {
  field: "nfiles",
  header: "",
  icon: ["fa", "file"],
  label: "Files",
  body: {
    component: FilesIconCounter,
    props: (row) => ({ count: row.nfiles }),
  },
};

/** When the item was last modified, as a relative date. */
export const LAST_MODIFIED_COLUMN = {
  field: "last_modified",
  header: "",
  label: "Last modified",
  icon: ["fa", "clock"],
  cellClass: "last-modified-cell",
  getValue: (row) => formatRelativeDate(row.last_modified),
};
