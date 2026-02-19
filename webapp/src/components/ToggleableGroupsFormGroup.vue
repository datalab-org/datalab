<template>
  <div
    ref="outerdiv"
    class="h-100 form-group clickable"
    @click="isEditingGroups = !isEditingGroups"
  >
    <label id="groups" class="clickable">
      Shared with Groups (read-only)
      <font-awesome-icon id="edit-icon" class="pl-1" icon="pen" size="xs" :fade="isEditingGroups" />
    </label>
    <div>
      <div v-if="!isEditingGroups">
        <div v-if="!value || value.length === 0" class="text-muted small">
          Not shared with any groups
        </div>
        <div v-else class="d-flex flex-wrap gap-2">
          <FormattedGroupName v-for="group in value" :key="group.immutable_id" :group="group" />
        </div>
      </div>
      <OnClickOutside
        v-if="isEditingGroups"
        :options="{ ignore: [outerDivRef] }"
        @trigger="isEditingGroups = false"
      >
        <GroupSelect v-model="shadowValue" multiple @click.stop />
      </OnClickOutside>
    </div>
  </div>
</template>

<script>
import { DialogService } from "@/services/DialogService";
import GroupSelect from "@/components/GroupSelect";
import FormattedGroupName from "@/components/FormattedGroupName.vue";
import { OnClickOutside } from "@vueuse/components";
import { updateItemPermissions, updateCollectionPermissions } from "@/server_fetch_utils.js";
import { toRaw } from "vue";

export default {
  components: {
    GroupSelect,
    FormattedGroupName,
    OnClickOutside,
  },
  props: {
    refcode: { type: String, required: false, default: null },
    collectionId: { type: String, required: false, default: null },
    modelValue: {
      type: Array,
      required: true,
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      isEditingGroups: false,
      outerDivRef: null,
      shadowValue: [],
    };
  },
  computed: {
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
    async isEditingGroups(newValue, oldValue) {
      if (newValue === false && oldValue === true) {
        const currentValue = Array.isArray(this.value) ? this.value : [];
        const shadowValue = Array.isArray(this.shadowValue) ? this.shadowValue : [];
        if (JSON.stringify(toRaw(currentValue)) === JSON.stringify(toRaw(shadowValue))) {
          return;
        }

        try {
          const confirmed = await DialogService.confirm({
            title: "Update Permissions",
            message: `Are you sure you want to update the group permissions of this ${
              this.collectionId ? "collection" : "item"
            }?`,
            type: "warning",
          });
          if (confirmed) {
            // Use the appropriate function based on whether it's a collection or item
            if (this.collectionId) {
              await updateCollectionPermissions(this.collectionId, null, this.shadowValue);
            } else {
              await updateItemPermissions(this.refcode, null, this.shadowValue);
            }
            this.$emit("update:modelValue", [...this.shadowValue]);
          } else {
            this.shadowValue = [...this.value];
          }
        } catch (error) {
          DialogService.error({
            title: "Permission Update Failed",
            message: "Error updating group permissions: " + error,
          });
          this.shadowValue = [...this.value];
        }
      }
    },
    modelValue: {
      immediate: true,
      handler(newVal) {
        const newArray = Array.isArray(newVal) ? [...newVal] : [];
        const currentArray = Array.isArray(this.shadowValue) ? this.shadowValue : [];

        if (JSON.stringify(currentArray) !== JSON.stringify(newArray)) {
          this.shadowValue = newArray;
        }
      },
    },
  },
  async mounted() {
    this.outerDivRef = this.$refs.outerdiv;
  },
};
</script>

<style scoped>
#edit-icon {
  color: grey;
}
</style>
