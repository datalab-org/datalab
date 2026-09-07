<template>
  <div class="container-lg">
    <div class="row">
      <div class="col">
        <div id="item-information" class="form-row">
          <div v-if="!hiddenFields.includes('name')" class="form-group col-sm-6 pr-2">
            <label for="item-name">Name</label>
            <input id="item-name" v-model="Name" class="form-control" />
          </div>
          <div v-if="!hiddenFields.includes('date')" class="form-group col-sm-6">
            <label for="item-date">Date Created</label>
            <input
              id="item-date"
              v-model="DateCreated"
              type="datetime-local"
              class="form-control"
            />
          </div>
        </div>

        <div class="form-row">
          <div v-if="!hiddenFields.includes('refcode')" class="form-group col-md-3 col-sm-4">
            <label for="item-refcode">Refcode</label>
            <div id="item-refcode"><FormattedRefcode :refcode="Refcode" /></div>
          </div>
          <div v-if="!hiddenFields.includes('status')" class="form-group col-md-3 col-sm-4">
            <ToggleableItemStatusFormGroup
              v-model="Status"
              :possible-item-statuses="possibleItemStatuses"
            />
          </div>
          <div v-if="!hiddenFields.includes('collections')" class="form-group col-md-6 col-sm-4">
            <ToggleableCollectionFormGroup v-model="Collections" />
          </div>
        </div>

        <div class="form-row">
          <div v-if="!hiddenFields.includes('creators')" class="form-group col-6 pb-3">
            <ToggleableCreatorsFormGroup v-model="Creators" :refcode="Refcode" />
          </div>
          <div v-if="!hiddenFields.includes('groups')" class="form-group col-6 pb-3">
            <ToggleableGroupsFormGroup v-model="Groups" :refcode="Refcode" />
          </div>
        </div>

        <div v-if="!hiddenFields.includes('location')" class="form-row">
          <div class="form-group col-12">
            <label for="item-location">Location</label>
            <LocationInput
              v-model="Location"
              :suggestions="knownLocations"
              input-id="item-location"
            />
          </div>
        </div>
      </div>

      <div v-if="!hiddenFields.includes('relationships')" class="col-md-4">
        <ItemRelationshipVisualization :item_id="item_id" />
      </div>
    </div>

    <div v-if="!hiddenFields.includes('description')" class="row">
      <div class="col">
        <label id="item-description-label">Description</label>
        <TiptapInline v-model="Description" aria-labelledby="item-description-label" />
      </div>
    </div>
  </div>
</template>

<script>
import { createComputedSetterForItemField } from "@/field_utils.js";
import FormattedRefcode from "@/components/FormattedRefcode.vue";
import ItemRelationshipVisualization from "@/components/ItemRelationshipVisualization.vue";
import LocationInput from "@/components/LocationInput.vue";
import TiptapInline from "@/components/TiptapInline.vue";
import ToggleableCollectionFormGroup from "@/components/ToggleableCollectionFormGroup.vue";
import ToggleableCreatorsFormGroup from "@/components/ToggleableCreatorsFormGroup.vue";
import ToggleableGroupsFormGroup from "@/components/ToggleableGroupsFormGroup.vue";
import ToggleableItemStatusFormGroup from "@/components/ToggleableItemStatusFormGroup.vue";

const DEFAULT_ITEM_STATUSES = ["active", "planned", "disposed", "completed", "failed", "other"];

function resolveEnum(schema, definitions) {
  if (!schema) return [];
  if (Array.isArray(schema.enum)) return schema.enum;
  if (schema.$ref) {
    const name = schema.$ref.split("/").pop();
    return resolveEnum(definitions?.[name], definitions);
  }
  for (const branch of schema.anyOf || []) {
    const values = resolveEnum(branch, definitions);
    if (values.length) return values;
  }
  return [];
}

export default {
  name: "ItemInformation",
  components: {
    FormattedRefcode,
    ItemRelationshipVisualization,
    LocationInput,
    TiptapInline,
    ToggleableCollectionFormGroup,
    ToggleableCreatorsFormGroup,
    ToggleableGroupsFormGroup,
    ToggleableItemStatusFormGroup,
  },
  props: {
    item_id: { type: String, required: true },
    hiddenFields: { type: Array, default: () => [] },
  },
  computed: {
    item() {
      return this.$store.state.all_item_data[this.item_id] || {};
    },
    schema() {
      return this.$store.state.schemas[this.item.type]?.attributes?.schema || {};
    },
    possibleItemStatuses() {
      const schemaStatuses = resolveEnum(this.schema.properties?.status, this.schema.$defs);
      return schemaStatuses.length ? schemaStatuses : DEFAULT_ITEM_STATUSES;
    },
    knownLocations() {
      return [
        ...new Set(
          [
            ...(this.$store.state.sample_list || []),
            ...(this.$store.state.starting_material_list || []),
            ...(this.$store.state.equipment_list || []),
          ]
            .map((item) => item.location)
            .filter(Boolean),
        ),
      ].sort();
    },
    Name: createComputedSetterForItemField("name"),
    DateCreated: createComputedSetterForItemField("date"),
    Refcode: createComputedSetterForItemField("refcode"),
    Status: createComputedSetterForItemField("status"),
    Collections: createComputedSetterForItemField("collections"),
    Creators: createComputedSetterForItemField("creators"),
    Groups: createComputedSetterForItemField("groups"),
    Location: createComputedSetterForItemField("location"),
    Description: createComputedSetterForItemField("description"),
  },
};
</script>
