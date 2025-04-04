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
    <img v-if="isPhoto" data-testid="media-block-img" :src="media_url" class="img-fluid mx-auto" />
    <video v-if="isVideo" :src="media_url" controls class="mx-auto" />
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import { createComputedSetterForBlockField } from "@/field_utils.js";
import { API_URL } from "@/resources.js";

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
    media_url() {
      // If the API has already base64 encoded the image, then use it,
      let b64_encoding = this.block_data["b64_encoded_image"] || null;
      if ((b64_encoding != null && b64_encoding[this.file_id]) || null != null) {
        return `data:image/png;base64,${b64_encoding[this.file_id]}`;
      }
      return `${API_URL}/files/${this.file_id}/${this.lookup_file_field("name", this.file_id)}`;
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
  },
  methods: {
    lookup_file_field(field, file_id) {
      return this.all_files.find((file) => file.immutable_id === file_id)?.[field];
    },
  },
};
</script>

<style scoped>
image,
video {
  display: block;
  max-height: 600px;
}
</style>
