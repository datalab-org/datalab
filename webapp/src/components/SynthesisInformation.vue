<template>
  <table class="table">
    <thead>
      <tr>
        <th>Component</th>
        <th>Formula</th>
        <th>Amount (g)</th>
      </tr>
    </thead>
    <tbody class="borderless">
      <tr v-for="(constituent, index) in constituents" :key="index">
        <td style="width: 70%">
          <vSelect
            v-model="constituent.item"
            :options="items"
            @search="debouncedAsyncSearch"
            label="name"
          >
            <template #no-options="{ searching }">
              <span v-if="searching"> Sorry, no matches found. </span>
              <span v-else class="empty-search"> Type a search term... </span>
            </template>
            <template v-slot:option="{ type, item_id, name, chemform }">
              <span
                class="badge badge-light mr-2"
                :style="{ backgroundColor: getBadgeColor(type) }"
              >
                {{ item_id }}
              </span>
              {{ name }}
              <template v-if="chemform && chemform != ' '">
                [ <ChemicalFormula :formula="chemform" /> ]
              </template>
            </template>
            <template v-slot:selected-option="{ type, item_id, name }">
              <span
                class="badge badge-light mr-2"
                :style="{ backgroundColor: getBadgeColor(type) }"
                >{{ item_id }}</span
              >
              {{ name }}
            </template>
          </vSelect>
        </td>
        <td style="width: 20%">
          <ChemicalFormula :formula="constituent.item?.chemform" />
        </td>
        <td style="width: 10%">
          <input v-model="constituent.quantity" />
        </td>
      </tr>
      <label class="mr-2">Synthesis procedure</label>
      <TinyMceInline v-model="SynthesisDescription"></TinyMceInline>

      <a
        type="button"
        class="new-component-button ml-2"
        aria-label="add component"
        @click="addConstituent"
      >
        <span aria-hidden="true">+</span>
      </a>
    </tbody>
  </table>
</template>

<script>
import { searchItems } from "@/server_fetch_utils.js";
import TinyMceInline from "@/components/TinyMceInline";
import vSelect from "@/../node_modules/vue-select-jdbocarsly/src/index.js";
import ChemicalFormula from "@/components/ChemicalFormula.vue";
import { itemTypes } from "@/resources.js";
import { createComputedSetterForItemField } from "@/field_utils.js";

export default {
  components: {
    TinyMceInline,
    vSelect,
    ChemicalFormula,
  },
  props: {
    item_id: String,
  },
  data() {
    return {
      debounceTimeout: null,
      isSearchFetchError: false,
      items: [],
    };
  },
  computed: {
    constituents: createComputedSetterForItemField("synthesis_constituents"),
    SynthesisDescription: createComputedSetterForItemField("synthesis_description"),
  },
  methods: {
    getBadgeColor(itemType) {
      return itemTypes[itemType]?.lightColor || "LightGrey";
    },
    getBadgeName(itemType) {
      return (itemTypes[itemType]?.navbarName || "").toLowerCase();
    },
    async debouncedAsyncSearch(query, loading) {
      loading(true);
      const debounceTime = 250; // time after user stops typing before request is sent
      clearTimeout(this.debounceTimeout); // reset the timer
      // start the timer
      this.debounceTimeout = setTimeout(async () => {
        await searchItems(query, 100, ["samples", "starting_materials"])
          .then((items) => {
            this.items = items;
          })
          .catch((error) => {
            console.error("Fetch error");
            console.error(error);
            this.isSearchFetchError = true;
          });
        loading(false);
      }, debounceTime);
    },
    addConstituent() {
      this.constituents.push({
        item: null,
        quantity: null,
      });
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
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
  color: #777;
  text-decoration: none;
}

th {
  font-weight: 300;
}

table {
  margin-bottom: 10rem;
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
