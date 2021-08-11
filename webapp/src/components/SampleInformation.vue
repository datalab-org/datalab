<template>
  <div class="container">
    <!-- Sample information -->
    <div class="form-row">
      <div class="form-group col-md-2">
        <label for="sample_id" class="mr-2">Sample ID</label>
        <input id="sample_id" class="form-control-plaintext" readonly="true" :value="sample_id" />
      </div>
      <div class="form-group col-md-7">
        <label for="name" class="mr-2">Name</label>
        <input id="name" class="form-control" v-model="Name" />
      </div>
      <div class="form-group col-md-3">
        <label for="date" class="mr-2">Date</label>
        <input v-model="DateCreated" type="date" class="form-control" />
      </div>
    </div>
    <!--    <div class="form-row">
      <div class="form-group col-md-4">
         <label for="chemform" class="mr-2">Chemical formula</label>
         <input id="chemform" class="form-control" v-model="ChemForm" />
      </div>
   </div> -->
    <div class="form-row">
      <div class="form-group col-md-3">
        <label for="chemform" class="mr-2">Chemical formula</label>
        <ChemFormulaInput v-model="ChemForm" />
      </div>
    </div>

    <label class="mr-2">Description</label>
    <TinyMceInline v-model="SampleDescription"></TinyMceInline>
  </div>
</template>

<script>
import { createComputedSetterForSampleField } from "@/field_utils.js";
import ChemFormulaInput from "@/components/ChemFormulaInput";
import TinyMceInline from "@/components/TinyMceInline";

export default {
  props: {
    sample_id: String,
  },
  computed: {
    SampleDescription: createComputedSetterForSampleField("description"),
    Name: createComputedSetterForSampleField("name"),
    ChemForm: createComputedSetterForSampleField("chemform"),
    DateCreated: createComputedSetterForSampleField("date"),
  },
  components: {
    ChemFormulaInput,
    TinyMceInline,
  },
};
</script>
