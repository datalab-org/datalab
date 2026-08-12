import { FilterOperator } from "@primevue/core/api";

export function matchStatus(value, filterValue) {
  if (!filterValue || (Array.isArray(filterValue) && filterValue.length === 0)) return true;
  if (Array.isArray(filterValue)) return filterValue.some((f) => f.status === value);
  return filterValue.status === value;
}

export function matchCollections(value, filterValue, operator) {
  if (!filterValue || !value) return true;
  const isAnd = operator === FilterOperator.AND;
  if (Array.isArray(filterValue)) {
    return isAnd
      ? filterValue.every((f) => value.some((c) => c.collection_id === f.collection_id))
      : filterValue.some((f) => value.some((c) => c.collection_id === f.collection_id));
  }
  return value.some((c) => c.collection_id === filterValue.collection_id);
}

export function matchCreatorsAndGroups(value, filterValue, operator) {
  if (!filterValue || !value) return true;
  const isAnd = operator === FilterOperator.AND;
  if (Array.isArray(filterValue)) {
    return isAnd
      ? filterValue.every((f) =>
          value.some((item) => item.display_name === f.display_name && item.type === f.type),
        )
      : filterValue.some((f) =>
          value.some((item) => item.display_name === f.display_name && item.type === f.type),
        );
  }
  return value.some(
    (item) => item.display_name === filterValue.display_name && item.type === filterValue.type,
  );
}

export function matchBlocks(value, filterValue, operator) {
  if (
    filterValue === null ||
    filterValue === undefined ||
    (Array.isArray(filterValue) && filterValue.length === 0)
  )
    return true;
  if (Array.isArray(filterValue) && filterValue.some((f) => f.blocktype === "__no_blocks__")) {
    if (!value || !Array.isArray(value) || value.length === 0) return true;
  }
  if (!value || !Array.isArray(value)) return false;
  const isAnd = operator === FilterOperator.AND;
  if (Array.isArray(filterValue)) {
    return isAnd
      ? filterValue.every((fb) =>
          fb.blocktype === "__no_blocks__"
            ? !value || value.length === 0
            : value.some((ib) => ib.blocktype === fb.blocktype),
        )
      : filterValue.some((fb) =>
          fb.blocktype === "__no_blocks__"
            ? !value || value.length === 0
            : value.some((ib) => ib.blocktype === fb.blocktype),
        );
  }
  return value.some((ib) => ib.blocktype === filterValue.blocktype);
}

export function matchStringValues(value, filterValue) {
  if (!filterValue || (Array.isArray(filterValue) && filterValue.length === 0)) return true;
  return Array.isArray(filterValue) ? filterValue.includes(value) : filterValue === value;
}

export function collectionsOptions(data) {
  return Array.from(
    new Map(
      data.flatMap((item) => item.collections || []).map((c) => [c.collection_id, c]),
    ).values(),
  );
}

export function creatorsAndGroupsOptions(data) {
  const allItems = data.flatMap((item) => item.creatorsAndGroups || []);
  const uniqueMap = new Map();
  allItems.forEach((item) => {
    const key = `${item.type}-${item.display_name}`;
    if (!uniqueMap.has(key)) uniqueMap.set(key, { ...item });
  });
  return Array.from(uniqueMap.values());
}

export function statusOptions(data) {
  return Array.from(new Set(data.filter((item) => item.status).map((item) => item.status))).map(
    (status) => ({ status }),
  );
}

export function blocksOptions(data, state) {
  const itemsWithBlocks = data.filter((item) => item.blocks && item.blocks.length > 0);
  const blocksInfos = state.blocksInfos || {};
  const blockTypesMap = new Map(
    itemsWithBlocks
      .flatMap((item) => item.blocks)
      .map((block) => [
        block.blocktype,
        {
          blocktype: block.blocktype,
          label: blocksInfos[block.blocktype]?.attributes?.name || block.blocktype,
        },
      ]),
  );
  blockTypesMap.set("__no_blocks__", { blocktype: "__no_blocks__", label: "No blocks" });
  return Array.from(blockTypesMap.values());
}

export function stringValuesOptions(field) {
  return (data) =>
    Array.from(new Set(data.filter((item) => item[field]).map((item) => item[field]))).sort();
}
