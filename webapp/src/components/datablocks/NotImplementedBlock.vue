<template>
  <DataBlockBase>
    <div class="alert alert-danger">
      This block type is not implemented/installed for this <i>datalab</i> instance. Please contact
      your <i>datalab</i> administrator.
    </div>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase.vue";

export default {
  components: {
    DataBlockBase,
  },
};
</script>
