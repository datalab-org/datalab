<template>
  <EditorBase :item_id="item_id">
    <SampleInformation :item_id="item_id" />
  </EditorBase>
</template>

<script>
import EditorBase from "@/components/EditorBase";
import SampleInformation from "@/components/SampleInformation";

export default {
  data() {
    return {
      item_id: this.$route.params.id,
    };
  },
  components: {
    EditorBase,
    SampleInformation,
  },
};
</script>
