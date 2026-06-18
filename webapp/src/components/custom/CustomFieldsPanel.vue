<template>
  <div v-if="customFields.length > 0" class="container custom-fields-panel mt-3">
    <div
      v-for="(section, sIdx) in sections"
      :key="section.title || sIdx"
      class="plugin-card"
      :class="{ 'mt-3': sIdx > 0 }"
    >
      <div v-if="section.title" class="plugin-card-header">
        <span>{{ section.title }}</span>
      </div>
      <hr v-else class="mt-0" />
      <div class="plugin-card-body">
        <!-- Renders scalar fields only: item-reference selectors, numbers, strings, enums,
             booleans. Structural fields (lists, nested objects) need a custom plugin panel.
             Fields can be grouped into separate cards via the `datalab_section` annotation. -->
        <div class="form-row mb-2">
          <div
            v-for="field in section.fields"
            :key="field.name"
            class="form-group col-md-6 col-lg-4"
          >
            <label :for="'custom-' + field.name">{{ field.title }}</label>

            <!-- Read-only -->
            <div v-if="field.readOnly" class="form-control-plaintext">
              {{ itemData[field.name] ?? "—" }}
            </div>

            <!-- Item reference: fixed link when selected, dropdown when empty -->
            <div v-else-if="field.refTypes">
              <div v-if="itemData[field.name]" class="input-group">
                <div class="form-control ref-display">
                  <FormattedItemName
                    :item_id="itemData[field.name].item_id"
                    :item-type="itemData[field.name].type"
                    :name="itemData[field.name].name || ''"
                    enable-click
                    enable-modified-click
                  />
                </div>
                <div class="input-group-append">
                  <button
                    type="button"
                    class="btn btn-outline-secondary"
                    title="Clear"
                    @click="updateField(field.name, null)"
                  >
                    <font-awesome-icon :icon="['fas', 'times']" />
                  </button>
                </div>
              </div>
              <ItemSelect
                v-else
                :model-value="itemData[field.name]"
                :types-to-query="field.refTypes"
                @update:model-value="updateField(field.name, $event)"
              />
            </div>

            <!-- Number with unit selector -->
            <div
              v-else-if="(field.type === 'number' || field.type === 'integer') && field.unitField"
              class="input-group"
            >
              <input
                :id="'custom-' + field.name"
                type="number"
                class="form-control"
                :step="field.type === 'integer' ? '1' : 'any'"
                :value="itemData[field.name] ?? ''"
                @change="
                  updateField(
                    field.name,
                    $event.target.value === '' ? null : Number($event.target.value),
                  )
                "
              />
              <div class="input-group-append">
                <select
                  class="form-control unit-select"
                  :value="itemData[field.unitField] ?? field.defaultUnit"
                  @change="updateField(field.unitField, $event.target.value)"
                >
                  <option v-for="u in field.unitOptions" :key="u" :value="u">{{ u }}</option>
                </select>
              </div>
            </div>

            <!-- Enum → select -->
            <select
              v-else-if="field.enum"
              :id="'custom-' + field.name"
              class="form-control"
              :value="itemData[field.name] ?? ''"
              @change="updateField(field.name, $event.target.value || null)"
            >
              <option value="">—</option>
              <option v-for="opt in field.enum" :key="opt" :value="opt">{{ opt }}</option>
            </select>

            <!-- Boolean → checkbox -->
            <div v-else-if="field.type === 'boolean'" class="form-check mt-2">
              <input
                :id="'custom-' + field.name"
                type="checkbox"
                class="form-check-input"
                :checked="itemData[field.name]"
                @change="updateField(field.name, $event.target.checked)"
              />
            </div>

            <!-- Plain number -->
            <input
              v-else-if="field.type === 'number' || field.type === 'integer'"
              :id="'custom-' + field.name"
              type="number"
              class="form-control"
              :step="field.type === 'integer' ? '1' : 'any'"
              :value="itemData[field.name] ?? ''"
              @change="
                updateField(
                  field.name,
                  $event.target.value === '' ? null : Number($event.target.value),
                )
              "
            />

            <!-- Multi-line string (datalab_multiline) -->
            <textarea
              v-else-if="field.multiline"
              :id="'custom-' + field.name"
              class="form-control"
              rows="2"
              :value="itemData[field.name] ?? ''"
              @change="updateField(field.name, $event.target.value || null)"
            ></textarea>

            <!-- String (default) -->
            <input
              v-else
              :id="'custom-' + field.name"
              type="text"
              class="form-control"
              :value="itemData[field.name] ?? ''"
              @change="updateField(field.name, $event.target.value || null)"
            />
          </div>
        </div>
      </div>
      <!-- plugin-card-body -->
    </div>
    <!-- plugin-card -->
  </div>
</template>

<script>
import { itemTypes, prettifyType } from "@/resources.js";
import ItemSelect from "@/components/ItemSelect.vue";
import FormattedItemName from "@/components/FormattedItemName.vue";

// Pydantic v2 emits nullable fields as anyOf: [{type: X}, {type: "null"}].
function unwrapNullable(schema) {
  if (!schema) return { schema: {}, nullable: false };
  if (schema.anyOf) {
    const nonNull = schema.anyOf.filter((s) => s.type !== "null");
    if (nonNull.length === 1) {
      return { schema: { ...schema, ...nonNull[0], anyOf: undefined }, nullable: true };
    }
  }
  return { schema, nullable: false };
}

// CustomFieldsPanel renders these directly; anything else (arrays, nested objects) is the
// responsibility of a custom plugin panel (a .vue component shipped by the plugin).
const SCALAR_TYPES = new Set(["string", "number", "integer", "boolean"]);

function resolveField(name, rawSchema) {
  const { schema } = unwrapNullable(rawSchema);
  const extra = rawSchema["x-json_schema_extra"] || rawSchema;
  return {
    name,
    title: rawSchema.title || prettifyType(name),
    description: rawSchema.description || null,
    type: schema.type || "string",
    enum: schema.enum || null,
    readOnly: rawSchema.readOnly === true,
    refTypes: extra.datalab_ref_types || null,
    // Optional grouping: fields sharing a `datalab_section` render in their own card.
    section: extra.datalab_section || null,
    // Render a long string as a multi-line <textarea> instead of a single-line input.
    multiline: extra.datalab_multiline === true,
    // Number+unit compound widget
    unitField: extra.datalab_unit_field || null,
    unitOptions: extra.units || null,
    defaultUnit: extra.default_unit || null,
  };
}

export default {
  name: "CustomFieldsPanel",
  components: { ItemSelect, FormattedItemName },
  props: {
    item_id: { type: String, required: true },
    itemType: { type: String, required: true },
  },
  computed: {
    itemData() {
      return this.$store.state.all_item_data[this.item_id] || {};
    },
    typeEntry() {
      return itemTypes[this.itemType];
    },
    typeSchema() {
      return this.$store.state.schemas[this.itemType]?.attributes?.schema || null;
    },
    baseType() {
      return this.typeSchema?.datalab_base_type || this.typeEntry?.baseType || null;
    },
    baseSchema() {
      return this.baseType
        ? this.$store.state.schemas[this.baseType]?.attributes?.schema || null
        : null;
    },
    sectionTitle() {
      return this.typeSchema?.datalab_section_title || null;
    },
    customFields() {
      if (!this.typeSchema || !this.baseSchema) return [];
      const typeProps = this.typeSchema.properties || {};
      const baseProps = this.baseSchema ? Object.keys(this.baseSchema.properties || {}) : [];

      return Object.entries(typeProps)
        .filter(([name, schema]) => {
          if (baseProps.includes(name) || name === "type") return false;
          const extra = schema["x-json_schema_extra"] || schema;
          if (extra.datalab_hidden) return false;
          // Render only scalar-ish fields. Item references (datalab_ref_types) and enums
          // are renderable too; structural fields (arrays/objects) need a custom panel.
          const { schema: unwrapped } = unwrapNullable(schema);
          const renderable =
            !!extra.datalab_ref_types || !!unwrapped.enum || SCALAR_TYPES.has(unwrapped.type);
          return renderable;
        })
        .map(([name, schema]) => resolveField(name, schema));
    },
    // Group fields into cards by their `datalab_section`. Ungrouped fields form the
    // default card (titled by `datalab_section_title`), which always renders first;
    // each distinct `datalab_section` then renders as its own titled card, in the order
    // the sections first appear in the schema.
    sections() {
      const groups = new Map();
      const order = [];
      for (const field of this.customFields) {
        const key = field.section || "__default__";
        if (!groups.has(key)) {
          groups.set(key, []);
          order.push(key);
        }
        groups.get(key).push(field);
      }
      const result = [];
      if (groups.has("__default__")) {
        result.push({ title: this.sectionTitle, fields: groups.get("__default__") });
      }
      for (const key of order) {
        if (key !== "__default__") result.push({ title: key, fields: groups.get(key) });
      }
      return result;
    },
  },
  methods: {
    updateField(fieldName, value) {
      this.$store.commit("updateItemData", {
        item_id: this.item_id,
        item_data: { [fieldName]: value },
      });
    },
  },
};
</script>

<style scoped>
.custom-fields-panel {
  padding-bottom: 1rem;
}
.plugin-card {
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  transition:
    box-shadow 0.15s ease,
    border-color 0.15s ease;
}
.plugin-card:hover {
  border-color: #adb5bd;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.07);
}
.plugin-card-header {
  font-size: 1rem;
  font-weight: 600;
  color: #495057;
  padding: 0.65rem 1rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  border-radius: 0.375rem 0.375rem 0 0;
}
.plugin-card-body {
  padding: 1rem;
}
.unit-select {
  border-left: 0;
  border-radius: 0 0.25rem 0.25rem 0;
  width: auto;
  min-width: 4.5rem;
}
/* Wraps a FormattedItemName so a selected reference reads as a filled field; the
   badge inside is the click target, so this box is intentionally not itself a link. */
.ref-display {
  display: flex;
  align-items: center;
  background-color: #f8f9fa;
  flex: 1;
}
</style>
