<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <FileSelectDropdown
      v-model="file_id"
      :item_id="item_id"
      :block_id="block_id"
      :extensions="['.png', '.jpg', '.jpeg']"
    />
    <div class="col-xl-6 col-lg-7 col-md-10 mx-auto">
      <img v-if="file_id" :src="image_url" class="img-fluid" />
    </div>
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
    image_url() {
      // return ''
      console.log("trying to get image_url for file_id:");
      console.log(this.file_id);
      // console.log(this.$store.state.files[this.file_id].url_path);

      return `${API_URL}/files/${this.file_id}/${this.all_files[this.file_id].name}`;
    },
  },
  components: {
    DataBlockBase,
    FileSelectDropdown,
  },
};
</script>
