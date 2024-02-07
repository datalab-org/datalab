<template>
  <div class="form-group">
    <label id="collections">
      Collections
      <font-awesome-icon
        class="clickable pl-1"
        icon="pen"
        size="xs"
        :fade="isEditingCollections"
        @click="isEditingCollections = !isEditingCollections"
      />
    </label>
    <div>
      <CollectionList
        v-if="!isEditingCollections"
        aria-labelledby="collections"
        :collections="value"
        style="padding-top: 0.5rem"
      />
      <OnClickOutside @trigger="isEditingCollections = false">
        <CollectionSelect
          v-if="isEditingCollections"
          aria-labelledby="collections"
          multiple
          v-model="value"
        />
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
    OnClickOutside,
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
.clickable {
  color: grey;
}

.text-heavy {
  font-weight: 600;
}
</style>
