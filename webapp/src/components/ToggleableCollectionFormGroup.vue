<template>
  <div
    class="h-100 form-group clickable"
    ref="outerdiv"
    @click="isEditingCollections = !isEditingCollections"
  >
    <label id="collections" class="clickable">
      Collections
      <font-awesome-icon
        id="edit-icon"
        class="pl-1"
        icon="pen"
        size="xs"
        :fade="isEditingCollections"
      />
    </label>
    <div>
      <CollectionList
        v-if="!isEditingCollections"
        aria-labelledby="collections"
        :collections="value"
      />
      <OnClickOutside
        v-if="isEditingCollections"
        :options="{ ignore: [outerDivRef] }"
        @trigger="isEditingCollections = false"
      >
        <CollectionSelect aria-labelledby="collections" multiple v-model="value" @click.stop />
      </OnClickOutside>
    </div>
  </div>
</template>

<script>
import CollectionSelect from "@/components/CollectionSelect";
import CollectionList from "@/components/CollectionList";
import { OnClickOutside } from "@vueuse/components";

export default {
  props: {
    modelValue: {},
  },
  data() {
    return {
      isEditingCollections: false,
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
  components: {
    CollectionSelect,
    CollectionList,
    OnClickOutside,
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
