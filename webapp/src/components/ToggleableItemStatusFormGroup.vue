<template>
  <div
    ref="outerdiv"
    class="h-100 form-group clickable"
    @click="isEditingStatus = !isEditingStatus"
  >
    <label for="item-status">
      Status
      <font-awesome-icon id="edit-icon" class="pl-1" icon="pen" size="xs" :fade="isEditingStatus" />
    </label>
    <div>
      <FormattedItemStatus v-if="!isEditingStatus" :status="value" aria-labelledby="status" />
      <OnClickOutside
        v-if="isEditingStatus"
        :options="{ ignore: [outerDivRef] }"
        @trigger="isEditingStatus = false"
      >
        <StatusSelect
          v-model="value"
          :options="possibleItemStatuses"
          aria-labelledby="status"
          @click.stop
        />
      </OnClickOutside>
    </div>
  </div>
</template>

<script>
import { OnClickOutside } from "@vueuse/components";
import StatusSelect from "@/components/StatusSelect.vue";
import FormattedItemStatus from "@/components/FormattedItemStatus.vue";

export default {
  components: {
    OnClickOutside,
    StatusSelect,
    FormattedItemStatus,
  },
  props: {
    modelValue: {
      type: String,
      default: "",
    },
    possibleItemStatuses: {
      type: Array,
      required: true,
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      isEditingStatus: false,
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
