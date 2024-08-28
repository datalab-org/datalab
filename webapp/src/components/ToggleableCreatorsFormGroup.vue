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
      <Creators v-if="!isEditingCreators" aria-labelledby="creators" :creators="value" />
      <OnClickOutside
        v-if="isEditingCreators"
        :options="{ ignore: [outerDivRef] }"
        @trigger="isEditingCreators = false"
      >
        <UserSelect v-model="shadow" aria-labelledby="creators" multiple @click.stop />
      </OnClickOutside>
    </div>
  </div>
</template>

<script>
import Creators from "@/components/Creators";
import UserSelect from "@/components/UserSelect";
import { OnClickOutside } from "@vueuse/components";

export default {
  components: {
    UserSelect,
    Creators,
    OnClickOutside,
  },
  props: {
    modelValue: {
      type: String,
      default: "",
    },
    shadowValue: {
      type: String,
      default: "",
    },
  },
  emits: ["update:modelValue", "update:shadowValue"],
  data() {
    return {
      isEditingCreators: false,
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
        this.$emit("update:shadowValue", newValue);
      },
    },
    shadow: {
      get() {
        return this.shadowValue;
      },
      set(newValue) {
        this.$emit("update:shadowValue", newValue);
      },
    },
  },
  watch: {
    isEditingCreators(newVal) {
      if (!newVal) {
        this.value = this.shadow;
      } else {
        this.shadow = this.value;
      }
    },
  },
  mounted() {
    this.outerDivRef = this.$refs.outerdiv; // we need to get the editIcon's ref to be accessible in the template so we can exclude it from the ClickOutside
    this.shadow = this.value;
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
