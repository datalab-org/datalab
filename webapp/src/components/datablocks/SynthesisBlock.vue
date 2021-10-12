<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <table class="table">
      <thead>
        <tr>
          <th>Component</th>
          <th>Name</th>
          <th>Formula</th>
          <th>Amount (g)</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(constituent, index) in constituents" :key="index">
          <td style="width: 25%">
            <vSelect v-model="constituent.sample" :options="samples" label="item_id" />
          </td>
          <td style="width: 33.33%">
            {{ constituent.sample && constituent.sample.name ? constituent.sample.name : null }}
          </td>
          <td
            style="width: 25%"
            v-html="
              constituent.sample && constituent.sample.chemform
                ? chemFormulaFormat(constituent.sample.chemform)
                : null
            "
          ></td>
          <td style="width: 16.67%">
            <input v-if="constituent.sample" />
          </td>
        </tr>
        <a
          type="button"
          class="new-component-button ml-2"
          aria-label="add component"
          @click="addComponent"
        >
          <span aria-hidden="true">+</span>
        </a>
      </tbody>
    </table>
  </DataBlockBase>
  <!-- 	<div class="form-inline">
		<div class="form-group">
			<label><b>Select a sample:</b></label>
			<vSelect style="width:10em" :options="['option1', 'option2', 'option3']" />
		</div>
	</div>
 -->
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import { getSampleList } from "@/server_fetch_utils.js";
import vSelect from "@/../node_modules/vue-select/src/index.js";
// import Multiselect from "@vueform/multiselect";
// import {createComputedSetterForBlockField} from "@/field_utils.js"

export default {
  components: {
    DataBlockBase,
    vSelect,
  },
  props: {
    item_id: String,
    block_id: String,
  },
  data() {
    return {
      isSampleFetchError: false,
      sample: null,
      constituents: [
        {
          sample: null,
          quantity: null,
        },
      ],
    };
  },
  computed: {
    samples() {
      return this.$store.state.sample_list;
    },
  },
  mounted() {
    this.getSamples();
  },
  methods: {
    getSamples() {
      getSampleList().catch((error) => {
        console.error("Fetch error");
        console.error(error);
        this.isSampleFetchError = true;
      });
    },
    chemFormulaFormat(chemform) {
      var re = /([\d.]+)/g;
      return chemform.replace(re, "<sub>$1</sub>");
    },
    addComponent() {
      this.constituents.push({
        sample: null,
        quantity: null,
      });
    },
  },
};
</script>
<!-- <style src="@vueform/multiselect/themes/default.css"></style>
 -->
<style scoped>
.new-component-button {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
  color: #777;
  text-decoration: none;
}

.new-component-button:hover {
  color: #555;
}
</style>
