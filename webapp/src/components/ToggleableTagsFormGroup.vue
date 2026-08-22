<template>
  <div ref="outerdiv" class="h-100 form-group clickable" @click="isEditingTags = !isEditingTags">
    <label id="tags" class="clickable">
      Tags
      <font-awesome-icon id="edit-icon" class="pl-1" icon="pen" size="xs" :fade="isEditingTags" />
      <router-link
        to="/tags"
        target="_blank"
        class="manage-tags-link pl-1"
        title="Manage tags"
        aria-label="Manage tags"
        @click.stop
      >
        <font-awesome-icon icon="cog" size="xs" />
      </router-link>
    </label>
    <div>
      <TagList v-if="!isEditingTags" aria-labelledby="tags" :tags="value" />
      <OnClickOutside
        v-if="isEditingTags"
        :options="{ ignore: [outerDivRef] }"
        @trigger="isEditingTags = false"
      >
        <TagSelect ref="tagSelect" v-model="value" aria-labelledby="tags" @click.stop />
      </OnClickOutside>
    </div>
  </div>
</template>

<script>
import TagSelect from "@/components/TagSelect";
import TagList from "@/components/TagList";
import { OnClickOutside } from "@vueuse/components";

export default {
  components: {
    TagSelect,
    TagList,
    OnClickOutside,
  },
  props: {
    modelValue: {
      type: Array,
      default: () => [],
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      isEditingTags: false,
      outerDivRef: null,
    };
  },
  computed: {
    // computed setter to pass v-model through the component:
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
    // expose the outer div ref so it can be excluded from the click-outside handler
    this.outerDivRef = this.$refs.outerdiv;
  },
};
</script>

<style scoped>
#edit-icon {
  color: grey;
}
.manage-tags-link {
  color: grey;
}
.manage-tags-link:hover {
  color: #0b6093;
}
</style>
