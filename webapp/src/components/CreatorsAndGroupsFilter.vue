<template>
  <MultiSelect
    :model-value="modelValue"
    :options="options"
    option-label="display_name"
    placeholder="Any"
    class="d-flex w-full"
    :filter="true"
    @update:model-value="$emit('update:modelValue', $event)"
    @click.stop
  >
    <template #option="slotProps">
      <div class="flex items-center">
        <UserBubble
          v-if="slotProps.option.type === 'creator'"
          :creator="slotProps.option"
          :size="24"
        />
        <FormattedGroupName
          v-if="slotProps.option.type === 'group'"
          :group="slotProps.option"
          :size="24"
        />
        <span v-if="slotProps.option.type === 'creator'" class="ml-1">{{
          slotProps.option.display_name
        }}</span>
      </div>
    </template>
    <template #value="slotProps">
      <div class="flex flex-wrap gap-2 items-center">
        <template v-if="slotProps.value && slotProps.value.length">
          <span
            v-for="(option, index) in slotProps.value"
            :key="index"
            class="inline-flex items-center mr-2"
          >
            <UserBubble v-if="option.type === 'creator'" :creator="option" :size="20" />
            <FormattedGroupName v-if="option.type === 'group'" :group="option" :size="20" />
            <span v-if="option.type === 'creator'" class="ml-1">{{ option.display_name }}</span>
          </span>
        </template>
        <span v-else class="text-gray-400">Any</span>
      </div>
    </template>
  </MultiSelect>
</template>

<script>
import MultiSelect from "primevue/multiselect";
import UserBubble from "@/components/UserBubble.vue";
import FormattedGroupName from "@/components/FormattedGroupName.vue";

export default {
  components: { MultiSelect, UserBubble, FormattedGroupName },
  props: {
    modelValue: { type: Array, default: null },
    options: { type: Array, default: () => [] },
  },
  emits: ["update:modelValue"],
};
</script>
