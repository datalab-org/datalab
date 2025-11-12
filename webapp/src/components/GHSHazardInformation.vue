<template>
  <div ref="outerdiv" class="h-100 form-group clickable">
    <FieldLabelDescriptionTooltip
      html-for="GHS-codes"
      label="GHS Hazard Information"
      :description="description"
    />
    <input
      v-model="value"
      type="text"
      class="form-control mb-2"
      aria-labelledby="startmat-hazards"
      :readonly="!editable"
      placeholder="Enter GHS hazard codes in free-text (e.g., H200, H203)"
      @click.stop
    />
    <GHSHazardPictograms v-model="value" aria-labelledby="startmat-hazards" />
  </div>
</template>

<script>
import GHSHazardPictograms from "@/components/GHSHazardPictograms";
import FieldLabelDescriptionTooltip from "@/components/FieldLabelDescriptionTooltip";

export default {
  components: {
    GHSHazardPictograms,
    FieldLabelDescriptionTooltip,
  },
  props: {
    modelValue: {
      type: String,
      default: "",
    },
    editable: {
      type: Boolean,
      default: false,
    },
    description: {
      type: String,
      default: null,
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      outerDivRef: null,
    };
  },
  computed: {
    // computed setter to pass v-model through  component:
    value: {
      get() {
        return this.modelValue;
      },
      set(newValue) {
        this.$emit("update:modelValue", newValue);
      },
    },
  },
  mounted() {
    this.outerDivRef = this.$refs.outerdiv; // we need to get the editIcon's ref to be accessible in the template so we can exclude it from the ClickOutside
  },
};
</script>

<style scoped>
.text-italic {
  opacity: 0.7;
}

#edit-icon {
  color: grey;
}

.text-heavy {
  font-weight: 600;
}
</style>
