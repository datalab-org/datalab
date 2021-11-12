<template>
  <div id="synthesis-information">
    <label class="mr-2">Synthesis Information</label>
    <table class="table">
      <thead>
        <tr class="subheading">
          <th>Component</th>
          <th>Formula</th>
          <th>Amount (g)</th>
        </tr>
      </thead>
      <tbody class="borderless">
        <tr v-for="(constituent, index) in constituents" :key="index">
          <td style="width: 70%">
            <ItemSelect v-model="constituent.item" />
          </td>
          <td style="width: 20%">
            <ChemicalFormula :formula="constituent.item?.chemform" />
          </td>
          <td style="width: 10%">
            <input v-model="constituent.quantity" />
          </td>
          <td>
            <button
              type="button"
              class="close"
              @click.stop="removeConstituent(index)"
              aria-label="delete"
            >
              <span aria-hidden="true">&times;</span>
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="row">
      <a
        type="button"
        class="new-component-button ml-2"
        aria-label="add component"
        @click="addConstituent"
      >
        <span aria-hidden="true">+</span> Add component
      </a>
    </div>
    <span class="subheading ml-2">Procedure</span>
    <TinyMceInline v-model="SynthesisDescription"></TinyMceInline>
  </div>
</template>

<script>
import TinyMceInline from "@/components/TinyMceInline";
import ChemicalFormula from "@/components/ChemicalFormula.vue";
import { createComputedSetterForItemField } from "@/field_utils.js";

import ItemSelect from "@/components/ItemSelect.vue";

export default {
  components: {
    TinyMceInline,
    ChemicalFormula,
    ItemSelect,
  },
  props: {
    item_id: String,
  },
  computed: {
    constituents: createComputedSetterForItemField("synthesis_constituents"),
    SynthesisDescription: createComputedSetterForItemField("synthesis_description"),
  },
  methods: {
    addConstituent() {
      this.constituents.push({
        item: null,
        quantity: null,
      });
    },
    removeConstituent(index) {
      this.constituents.splice(index, 1);
    },
  },
  mounted() {
    if (this.constituents.length == 0) {
      this.addConstituent();
    }
  },
};
</script>

<style scoped>
.new-component-button {
  line-height: 1;
  color: #777;
  text-decoration: none;
  padding-left: 2rem;
  padding-bottom: 1rem;
}

.new-component-button span {
  font-size: 2rem;
  font-weight: 700;
}

.subheading {
  color: darkslategrey;
  font-size: small;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 0px;
}

table {
  margin-bottom: 0rem;
}

.borderless td,
.borderless th {
  border: none;
}
.new-component-button:hover {
  color: #555;
}

.empty-search {
  opacity: 0.5;
  font-style: italic;
}
</style>
