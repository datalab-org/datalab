<template>
  <div class="container">
    <!-- Sample information -->
    <div class="form-row">
      <div class="form-group col-md-2">
        <label for="item_id" class="mr-2">Sample ID</label>
        <input id="item_id" class="form-control-plaintext" readonly="true" :value="item_id" />
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
    <div class="form-row">
      <div class="form-group col-md-3">
        <label for="chemform" class="mr-2">Chemical formula</label>
        <ChemFormulaInput v-model="ChemForm" />
      </div>
    </div>

    <label class="mr-2">Description</label>
    <TinyMceInline v-model="SampleDescription"></TinyMceInline>
    <label class="mr-2">Synthesis Information</label>
    <SynthesisInformation :item_id="item_id" />
  </div>
</template>

<script>
import { createComputedSetterForItemField } from "@/field_utils.js";
import ChemFormulaInput from "@/components/ChemFormulaInput";
import TinyMceInline from "@/components/TinyMceInline";
import SynthesisInformation from "@/components/SynthesisInformation";

export default {
  props: {
    item_id: String,
  },
  computed: {
    SampleDescription: createComputedSetterForItemField("description"),
    Name: createComputedSetterForItemField("name"),
    ChemForm: createComputedSetterForItemField("chemform"),
    DateCreated: createComputedSetterForItemField("date"),
  },
  components: {
    ChemFormulaInput,
    TinyMceInline,
    SynthesisInformation,
  },
};
</script>
