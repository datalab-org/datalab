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
        <div v-if="value.length === 0" class="text-muted small">Not shared with any groups</div>
        <div v-else class="d-flex flex-wrap">
          <span
            v-for="group in value"
            :key="group.immutable_id"
            class="badge badge-secondary mr-1 mb-1"
          >
            {{ group.display_name }}
          </span>
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
import { OnClickOutside } from "@vueuse/components";
import { updateItemPermissions } from "@/server_fetch_utils.js";
import { toRaw } from "vue";

export default {
  components: {
    GroupSelect,
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
        if (JSON.stringify(toRaw(this.value)) === JSON.stringify(toRaw(this.shadowValue))) {
          return;
        }

        try {
          let answer = confirm(
            "Are you sure you want to update the group permissions of this item?",
          );
          if (answer) {
            await updateItemPermissions(this.refcode, null, this.shadowValue);
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
        this.shadowValue = [...newVal];
      },
    },
  },
  async mounted() {
    this.outerDivRef = this.$refs.outerdiv;
  },
};
</script>
