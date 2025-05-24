<template>
  <div
    ref="outerdiv"
    class="h-100 form-group clickable"
    @click="isEditingCreators = !isEditingCreators"
  >
    <label id="creators" class="clickable">
      Creators
      <font-awesome-icon
        id="edit-icon"
        class="pl-1"
        icon="pen"
        size="xs"
        :fade="isEditingCreators"
      />
    </label>
    <div>
      <Creators
        v-if="!isEditingCreators"
        :show-names="value.length <= 1"
        aria-labelledby="creators"
        :creators="shadowValue"
      />
      <OnClickOutside
        v-if="isEditingCreators"
        :options="{ ignore: [outerDivRef] }"
        @trigger="isEditingCreators = false"
      >
        <UserSelect v-model="shadowValue" aria-labelledby="creators" multiple @click.stop />
      </OnClickOutside>
    </div>
  </div>
</template>

<script>
import { DialogService } from "@/services/DialogService";

import Creators from "@/components/Creators";
import UserSelect from "@/components/UserSelect";
import { OnClickOutside } from "@vueuse/components";
import { updateItemPermissions } from "@/server_fetch_utils.js";
import { toRaw } from "vue";

export default {
  components: {
    UserSelect,
    Creators,
    OnClickOutside,
  },
  props: {
    refcode: { type: String, required: true },
    modelValue: {
      type: Array,
      required: true,
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      isEditingCreators: false,
      outerDivRef: null,
      shadowValue: [],
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
  watch: {
    async isEditingCreators(newValue, oldValue) {
      // Check we are leaving the editing state
      if (newValue === false && oldValue === true) {
        // Check that the permissions have actually changed
        if (JSON.stringify(toRaw(this.value)) === JSON.stringify(toRaw(this.shadowValue))) {
          return;
        }
        try {
          // Check if the user has just removed all creators and reset if so
          if (this.shadowValue.length == 0) {
            throw new Error("You must have at least one creator.");
          }
          const confirmed = await DialogService.confirm({
            title: "Update Permissions",
            message: "Are you sure you want to update the permissions of this item?",
            type: "warning",
          });
          if (confirmed) {
            await updateItemPermissions(this.refcode, this.shadowValue);
            this.$emit("update:modelValue", [...this.shadowValue]);
          } else {
            this.shadowValue = [...this.value];
          }
        } catch (error) {
          // Reset value to original
          DialogService.error({
            title: "Permission Update Failed",
            message: "Error updating permissions: " + error,
          });
          this.shadowValue = [...this.value];
        }
      }
    },
    modelValue: {
      immediate: true,
      handler(newVal) {
        if (this.shadowValue !== newVal) {
          this.shadowValue = [...newVal];
        }
      },
    },
  },
  async mounted() {
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
