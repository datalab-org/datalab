<template>
  <div v-if="schema?.properties" class="container-lg">
    <div class="row">
      <div class="col-md-8">
        <div :id="`${item_data?.type}-information`">
          <div v-for="(row, rowIndex) in schema.layout" :key="rowIndex" class="form-row">
            <DynamicFieldRenderer
              v-for="fieldName in row"
              :key="fieldName"
              v-model="localItemData[fieldName]"
              :field-name="fieldName"
              :field-schema="schema.properties[fieldName]"
              :is-required="schema.required?.includes(fieldName)"
              :item-type="item_data.type"
              :item-data="localItemData"
              @update:model-value="handleFieldUpdate(fieldName, $event)"
            />
          </div>
        </div>
      </div>

      <div v-if="hasRelationships" class="col-md-4">
        <ItemRelationshipVisualization
          :item_id="item_data.item_id"
          :refcode="item_data.refcode"
          :relationships="item_data.relationships"
        />
      </div>
    </div>
  </div>
</template>

<script>
import DynamicFieldRenderer from "@/components/DynamicFieldRenderer.vue";
import ItemRelationshipVisualization from "@/components/ItemRelationshipVisualization";
import { getSchema } from "@/server_fetch_utils";

export default {
  components: {
    DynamicFieldRenderer,
    ItemRelationshipVisualization,
  },
  props: {
    item_data: { type: Object, required: true },
  },
  emits: ["update-item-data"],
  data() {
    return {
      schema: null,
      localItemData: { ...this.item_data },
    };
  },
  computed: {
    hasRelationships() {
      return ["samples", "cells", "starting_materials", "collections"].includes(
        this.item_data.type,
      );
    },
    tableOfContentsSections() {
      return this.getTableOfContentsSections();
    },
  },
  watch: {
    item_data: {
      handler(newVal) {
        this.localItemData = { ...newVal };
      },
      deep: true,
    },
  },
  async mounted() {
    const response = await getSchema(this.item_data.type);
    this.schema = response?.attributes?.schema || response?.attributes || response;
  },
  methods: {
    handleFieldUpdate(field, value) {
      this.localItemData[field] = value;
      this.$emit("update-item-data", { [field]: value });
    },
    getTableOfContentsSections() {
      const sections = [];

      sections.push({
        anchor: `${this.item_data.type}-information`,
        text: "Item Information",
      });

      if (this.item_data.type === "cells" && this.item_data.characteristic_mass) {
        sections.push({
          anchor: "cell-preparation-information",
          text: "Cell Preparation Information",
        });
      }

      return sections;
    },
  },
};
</script>
