<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <FileSelectDropdown
      v-model="file_id"
      :item_id="item_id"
      :block_id="block_id"
      :extensions="['.png', '.jpeg', '.jpg', '.mp4', '.mov', '.webm']"
      class="mb-3"
    />
    <img v-if="isPhoto" :src="media_url" class="img-fluid mx-auto" />
    <video v-if="isVideo" :src="media_url" controls class="mx-auto" />
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import { createComputedSetterForBlockField } from "@/field_utils.js";
import { API_URL } from "@/resources.js";

export default {
  props: {
    item_id: String,
    block_id: String,
  },
  computed: {
    file_id: createComputedSetterForBlockField("file_id"),
    all_files() {
      return this.$store.state.files;
    },
    media_url() {
      return `${API_URL}/files/${this.file_id}/${this.all_files[this.file_id].name}`;
    },
    isPhoto() {
      return [".png", ".jpeg", ".jpg"].includes(this.all_files[this.file_id]?.extension);
    },
    isVideo() {
      return [".mp4", ".mov", ".webm"].includes(this.all_files[this.file_id]?.extension);
    },
  },
  components: {
    DataBlockBase,
    FileSelectDropdown,
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
