<template>
  <div class="form-group">
    <label id="collections">
      Collections
      <span
        class="clickable text-italic"
        :class="{ 'text-heavy': isEditingCollections }"
        @click="isEditingCollections = !isEditingCollections"
        >[edit]</span
      >
    </label>
    <div>
      <CollectionList
        v-if="!isEditingCollections"
        aria-labelledby="collections"
        :collections="value"
      />
      <CollectionSelect
        v-if="isEditingCollections"
        aria-labelledby="collections"
        multiple
        v-model="value"
      />
    </div>
  </div>
</template>

<script>
import CollectionSelect from "@/components/CollectionSelect";
import CollectionList from "@/components/CollectionList";

export default {
  props: {
    modelValue: {},
  },
  data() {
    return {
      isEditingCollections: false,
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
  components: {
    CollectionSelect,
    CollectionList,
  },
};
</script>

<style scoped>
.clickable {
  cursor: pointer;
}

.text-italic {
  opacity: 0.7;
}

.text-heavy {
  font-weight: 600;
}
</style>
