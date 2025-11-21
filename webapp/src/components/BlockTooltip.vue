<template>
  <TooltipIcon v-if="showIcon">
    <h4 class="tooltip-title">{{ blockName }}</h4>
    <p v-if="blockVersion" class="block-version">Version: {{ blockVersion }}</p>
    <p>{{ blockDescription }}</p>
    <div v-if="acceptedExtensions && acceptedExtensions.length > 0">
      Accepted file extensions:
      <ul class="mb-0">
        <li v-for="(extension, index) in acceptedExtensions" :key="index" class="filetype-li">
          {{ extension }}
        </li>
      </ul>
    </div>
  </TooltipIcon>
  <StyledTooltip v-else :placement="'bottom-start'" :delay="500" anchor-display="block">
    <template #anchor>
      <a class="dropdown-item" tabindex="0">
        {{ blockName }}
      </a>
    </template>
    <template #content>
      <h4 class="tooltip-title">{{ blockName }}</h4>
      <p v-if="blockVersion" class="block-version">Version: {{ blockVersion }}</p>
      <p>{{ blockDescription }}</p>
      <p v-if="acceptedExtensions && acceptedExtensions.length > 0" class="accepted-file mb-0">
        Accepted file extensions:
        <span v-for="(extension, index) in acceptedExtensions" :key="index">
          {{ extension }}{{ index < acceptedExtensions.length - 1 ? ", " : "" }}
        </span>
      </p>
    </template>
  </StyledTooltip>
</template>

<script>
import StyledTooltip from "@/components/StyledTooltip";
import TooltipIcon from "@/components/TooltipIcon";

export default {
  name: "BlockTooltip",
  components: {
    StyledTooltip,
    TooltipIcon,
  },
  props: {
    blockInfo: {
      type: Object,
      required: true,
    },
    showIcon: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    blockName() {
      return this.blockInfo.attributes?.name || this.blockInfo.name;
    },
    blockDescription() {
      return this.blockInfo.attributes?.description || this.blockInfo.description;
    },
    blockVersion() {
      return this.blockInfo.attributes?.version || this.blockInfo.version;
    },
    acceptedExtensions() {
      return (
        this.blockInfo.attributes?.accepted_file_extensions ||
        this.blockInfo.accepted_file_extensions
      );
    },
  },
};
</script>

<style scoped>
.block-version {
  font-size: 0.85em;
  color: #aaa;
  font-style: italic;
  margin-bottom: 0.5em;
}
</style>
