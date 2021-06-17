<template>

<EditorBase :sample_id="sample_id">
   <SampleInformation :sample_id="sample_id" />
</EditorBase>
   
</template>

<script>

import EditorBase from "@/components/EditorBase"
import SampleInformation from "@/components/SampleInformation"

export default {
   data() {
      return {
         sample_id: this.$route.params.id,
      }
   },
   components: {
      EditorBase,
      SampleInformation
   }
}

</script>