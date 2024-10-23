<template>
  <div v-if="schema?.properties" class="container-lg">
    <div class="row">
      <div class="col">
        <div class="form-row">
          <div
            v-for="(field, index) in Object.keys(schema.properties)"
            :key="index"
            class="col-md-4"
          >
            <label v-if="field != 'relationships' && field != 'collections'" :for="field">{{
              schema.properties[field].title
            }}</label>

            <component
              :is="getComponentType(field)"
              :key="index"
              :placeholder="field.title"
              v-bind="getComponentProps(field)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getSchema } from "@/server_fetch_utils";
// import { createComputedSetterForItemField } from "@/field_utils.js";
import FormattedItemName from "@/components/FormattedItemName";
import FormattedRefcode from "@/components/FormattedRefcode";
import Creators from "@/components/Creators";
import ToggleableCollectionFormGroup from "@/components/ToggleableCollectionFormGroup";
import TinyMceInline from "@/components/TinyMceInline";
import ItemRelationshipVisualization from "@/components/ItemRelationshipVisualization";

export default {
  props: {
    item_data: { type: Object, required: true },
  },
  data() {
    return {
      schema: null,
    };
  },
  async mounted() {
    this.schema = await getSchema(this.item_data.type);
  },
  methods: {
    getComponentType(field) {
      switch (field) {
        case "item_id":
          return FormattedItemName;
        case "refcode":
          return FormattedRefcode;
        case "creators":
          return Creators;
        case "collections":
          return ToggleableCollectionFormGroup;
        case "description":
          return TinyMceInline;
        case "relationships":
          return ItemRelationshipVisualization;

        default:
          return "input";
      }
    },
    getComponentProps(field) {
      const fieldSchema = this.schema.properties[field];
      const isComponentDefined = this.getComponentType(field) !== "input";

      if (isComponentDefined && field == "item_id") {
        return {
          itemType: this.item_data.type,
          item_id: this.item_data.item_id,
          enableClick: true,
        };
      } else if ((isComponentDefined && field === "description") || field === "collections") {
        return {
          modelValue: this.item_data[field],
        };
      } else if (isComponentDefined && field === "relationships") {
        return {
          item_id: this.item_data.item_id,
        };
      } else if (isComponentDefined) {
        return {
          [field]: this.item_data[field],
        };
      }

      return {
        value: this.item_data[field] !== undefined ? this.item_data[field] : "",
        class: "form-control",
        ...(fieldSchema.type === "date" && { type: "datetime-local" }),
        ...(fieldSchema.type === "string" && { type: "text" }),
        ...(fieldSchema.type === "integer" && { type: "number" }),
        ...(fieldSchema.type === "array" && { class: "form-control" }),
        ...(fieldSchema.type === "object" && { class: "form-control" }),
      };
    },
  },
};
</script>
