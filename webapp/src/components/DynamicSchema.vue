<template>
  <div v-if="schema?.properties && data">
    <div v-for="(field, index) in Object.keys(schema.properties)" :key="index">
      <label v-if="field != 'relationships'" :for="field">{{
        schema.properties[field].title
      }}</label>

      <component
        :is="getComponentType(field)"
        :key="index"
        :value="data[field]"
        :placeholder="field.title"
        v-bind="getComponentProps(field)"
      />
    </div>
  </div>
</template>

<script>
import { getSchema } from "@/server_fetch_utils";
import FormattedItemName from "@/components/FormattedItemName";
import FormattedRefcode from "@/components/FormattedRefcode";
import Creators from "@/components/Creators";
import ToggleableCollectionFormGroup from "@/components/ToggleableCollectionFormGroup";
import TinyMceInline from "@/components/TinyMceInline";
import ItemRelationshipVisualization from "@/components/ItemRelationshipVisualization";

export default {
  props: {
    modelValue: {
      type: Object,
      required: true,
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      schema: null,
    };
  },
  computed: {
    data() {
      return { ...this.modelValue };
    },
  },
  async mounted() {
    this.schema = await getSchema(this.data?.type);
  },
  methods: {
    getComponentType(field) {
      const fieldSchema = this.schema.properties[field];

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

        case fieldSchema.type:
          if (["date", "string", "integer", "object"].includes(fieldSchema.type)) {
            return "input";
          }
          if (fieldSchema.type === "array") {
            return "textarea";
          }

          return "input";
        default:
          return "input";
      }
    },

    getComponentProps(field) {
      const fieldSchema = this.schema.properties[field];

      if (field === "item_id") {
        return {
          itemType: this.data.type,
          item_id: this.data.item_id,
          enableClick: true,
        };
      }
      if (field === "refcode") {
        return {
          refcode: this.data.refcode,
        };
      }
      if (field === "creators") {
        return {
          creators: this.data.creators,
        };
      }
      if (field === "collections") {
        return {
          modelValue: this.data.collections,
        };
      }
      if (field === "description") {
        return {
          modelValue: this.data.description,
        };
      }
      if (field === "relationships") {
        return {
          item_id: this.data.item_id,
        };
      }

      if (fieldSchema.type === "date") {
        return {
          value: this.data[field],
          type: "datetime-local",
          class: "form-control",
        };
      }
      if (fieldSchema.type === "string") {
        return {
          value: this.data[field],
          type: "text",
          class: "form-control",
        };
      }
      if (fieldSchema.type === "integer") {
        return {
          value: this.data[field],
          type: "number",
          class: "form-control",
        };
      }
      if (fieldSchema.type === "array") {
        return {
          value: this.data[field].join(", "),
          class: "form-control",
        };
      }
      if (fieldSchema.type === "object") {
        return {
          value: JSON.stringify(this.data[field]),
          class: "form-control",
        };
      }

      return { readonly: true, disabled: true };
    },
  },
};
</script>
