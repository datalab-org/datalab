<template>
  <TooltipIcon :title="blockInfo.attributes.description">
    <h4 class="block-info-title">{{ blockInfo.attributes.name }}</h4>
    <p>{{ blockInfo.attributes.description }}</p>
    <div
      v-if="
        blockInfo.attributes.accepted_file_extensions != null &&
        blockInfo.attributes.accepted_file_extensions.length > 0
      "
    >
      Accepted file extensions:
      <ul class="mb-0">
        <li
          v-for="(extension, index) in blockInfo.attributes.accepted_file_extensions"
          :key="index"
          class="filetype-li"
        >
          {{ extension }}
        </li>
      </ul>
    </div>
  </TooltipIcon>
</template>

<script>
import TooltipIcon from "@/components/TooltipIcon";

export default {
  name: "StyledBlockInfo",
  components: {
    TooltipIcon,
  },
  props: {
    blockInfo: {
      type: Object,
      default: () => ({}),
    },
  },
};
</script>

<style scoped>
.block-info-title {
  text-decoration: underline;
  text-decoration-color: cornflowerblue;
  text-decoration-style: wavy;
  margin-top: 0;
  margin-bottom: 0.5em;
}

.filetype-li {
  font-family: var(--font-monospace);
}

p {
  margin: 0;
}
</style>
