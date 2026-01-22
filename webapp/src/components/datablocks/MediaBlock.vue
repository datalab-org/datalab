<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <FileSelectDropdown
      v-model="file_id"
      :item_id="item_id"
      :block_id="block_id"
      :extensions="blockInfo.attributes.accepted_file_extensions"
      class="mb-3"
      update-block-on-change
    />
    <div v-if="isPhoto" class="img-wrapper">
      <img
        v-if="isPhoto"
        data-testid="media-block-img"
        :src="media_url"
        class="img-fluid mx-auto"
      />
    </div>
    <div v-else-if="isVideo" class="video-wrapper">
      <video v-if="isVideo" :src="media_url" controls class="mx-auto" />
    </div>
    <div v-else-if="isPDF" class="pdf-wrapper">
      <iframe v-if="isPDF" :src="media_url" width="100%" height="100%" frameborder="0"></iframe>
    </div>
    <div v-else-if="isSVG" class="svg-wrapper">
      <div v-if="svgLoading" class="text-center p-3">Loading SVG...</div>
      <div v-else-if="svgError" class="text-danger p-3">Error loading SVG: {{ svgError }}</div>
      <div v-else class="svg-content" v-html="sanitizedSVG"></div>
    </div>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import { createComputedSetterForBlockField } from "@/field_utils.js";
import { API_URL } from "@/resources.js";
import { fetch_file } from "@/server_fetch_utils.js";
import DOMPurify from "dompurify";

export default {
  components: {
    DataBlockBase,
    FileSelectDropdown,
  },
  props: {
    item_id: {
      type: String,
      required: true,
    },
    block_id: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      svgContent: null,
      svgLoading: false,
      svgError: null,
    };
  },
  computed: {
    file_id: createComputedSetterForBlockField("file_id"),
    all_files() {
      return this.$store.state.all_item_data[this.item_id].files;
    },
    block_data() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id];
    },
    blockInfo() {
      return this.$store.state.blocksInfos["media"];
    },
    adminSuperUserMode() {
      return this.$store.state.adminSuperUserMode;
    },
    media_url() {
      // If the API has already base64 encoded the image, then use it,
      let b64_encoding = this.block_data["b64_encoded_image"] || null;
      if ((b64_encoding != null && b64_encoding[this.file_id]) || null != null) {
        return `data:image/png;base64,${b64_encoding[this.file_id]}`;
      }
      const baseUrl = `${API_URL}/files/${this.file_id}/${this.lookup_file_field("name", this.file_id)}`;
      return this.adminSuperUserMode ? `${baseUrl}?sudo=1` : baseUrl;
    },
    isPhoto() {
      let extension = this.lookup_file_field("extension", this.file_id);
      if (extension) {
        extension = extension.toLowerCase();
      }
      return [".png", ".jpeg", ".jpg", ".tif", ".tiff"].includes(extension);
    },
    isVideo() {
      let extension = this.lookup_file_field("extension", this.file_id);
      if (extension) {
        extension = extension.toLowerCase();
      }
      return [".mp4", ".mov", ".webm"].includes(extension);
    },
    isPDF() {
      let extension = this.lookup_file_field("extension", this.file_id);
      if (extension) {
        extension = extension.toLowerCase();
      }
      return extension === ".pdf";
    },
    isSVG() {
      let extension = this.lookup_file_field("extension", this.file_id);
      if (extension) {
        extension = extension.toLowerCase();
      }
      return extension === ".svg";
    },
    sanitizedSVG() {
      if (!this.svgContent) return "";
      // Configure DOMPurify to allow SVG elements but remove scripts and event handlers
      return DOMPurify.sanitize(this.svgContent, {
        USE_PROFILES: { svg: true, svgFilters: true },
        ADD_TAGS: ["use"], // Allow SVG <use> elements
        FORBID_TAGS: ["script", "style"], // Explicitly forbid scripts and styles
        FORBID_ATTR: ["onerror", "onload", "onclick"], // Remove event handlers
      });
    },
  },
  watch: {
    file_id: {
      immediate: true,
      handler() {
        if (this.isSVG) {
          this.loadSVG();
        }
      },
    },
  },
  methods: {
    lookup_file_field(field, file_id) {
      return this.all_files.find((file) => file.immutable_id === file_id)?.[field];
    },
    async loadSVG() {
      if (!this.file_id) {
        this.svgContent = null;
        return;
      }

      this.svgLoading = true;
      this.svgError = null;

      try {
        // Fetch SVG with 10MB size limit (default)
        const response = await fetch_file(this.media_url);
        this.svgContent = await response.text();
      } catch (error) {
        console.error("Error loading SVG:", error);
        this.svgError = error.message;
      } finally {
        this.svgLoading = false;
      }
    },
  },
};
</script>

<style scoped>
img,
video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.video-wrapper {
  resize: both;
  height: 600px;
  overflow: auto;
  display: inline-block;
}

.pdf-wrapper {
  display: inline-block;
  width: 100%;
  height: 600px;
}

.img-wrapper {
  resize: both;
  height: 600px;
  overflow: auto;
  display: inline-block;
}

.svg-wrapper {
  resize: both;
  height: 600px;
  overflow: auto;
  display: inline-block;
  width: 100%;
}

.svg-content {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.svg-content :deep(svg) {
  max-width: 100%;
  max-height: 100%;
  height: auto;
  width: auto;
}
</style>
