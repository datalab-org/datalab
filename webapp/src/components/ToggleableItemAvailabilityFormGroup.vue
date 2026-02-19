<template>
  <div
    ref="outerdiv"
    class="h-100 form-group clickable"
    @click="isEditingAvailability = !isEditingAvailability"
  >
    <label for="item-availability">
      Availability
      <font-awesome-icon
        id="edit-icon"
        class="pl-1"
        icon="pen"
        size="xs"
        :fade="isEditingAvailability"
      />
    </label>
    <div>
      <FormattedItemAvailability
        v-if="!isEditingAvailability"
        :dot-only="false"
        :availability="value"
        aria-labelledby="availability"
      />
      <OnClickOutside
        v-if="isEditingAvailability"
        :options="{ ignore: [outerDivRef] }"
        @trigger="isEditingAvailability = false"
      >
        <AvailabilitySelect
          v-model="value"
          :options="possibleItemAvailabilities"
          aria-labelledby="availability"
          @click.stop
        />
      </OnClickOutside>
    </div>
  </div>
</template>

<script>
import { OnClickOutside } from "@vueuse/components";
import AvailabilitySelect from "@/components/AvailabilitySelect.vue";
import FormattedItemAvailability from "@/components/FormattedItemAvailability.vue";

export default {
  components: {
    OnClickOutside,
    AvailabilitySelect,
    FormattedItemAvailability,
  },
  props: {
    modelValue: {
      type: String,
      default: "",
    },
    possibleItemAvailabilities: {
      type: Array,
      required: true,
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      isEditingAvailability: false,
      outerDivRef: null,
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
  mounted() {
    this.outerDivRef = this.$refs.outerdiv;
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
