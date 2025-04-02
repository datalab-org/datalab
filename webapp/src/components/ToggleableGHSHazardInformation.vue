<template>
  <div ref="outerdiv" class="h-100 form-group clickable" @click="isEditing = !isEditing">
    <label id="startmat-hazards" class="clickable">
      GHS Hazard Codes
      <font-awesome-icon id="edit-icon" class="pl-1" icon="pen" size="xs" :fade="isEditing" />
    </label>
    <div>
      <GHSHazardInformation v-if="!isEditing" v-model="value" aria-labelledby="startmat-hazards" />
      <OnClickOutside
        v-if="isEditing"
        :options="{ ignore: [outerDivRef] }"
        @trigger="isEditing = false"
      >
        <input
          v-model="value"
          type="text"
          class="form-control"
          aria-labelledby="startmat-hazards"
          placeholder="Enter GHS hazard codes in free-text (e.g., H200, H203)"
          @click.stop
        />
      </OnClickOutside>
    </div>
  </div>
</template>

<script>
import GHSHazardInformation from "@/components/GHSHazardInformation";
import { OnClickOutside } from "@vueuse/components";

export default {
  components: {
    GHSHazardInformation,
    OnClickOutside,
  },
  props: {
    modelValue: {
      type: String,
      default: "",
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      isEditing: false,
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
