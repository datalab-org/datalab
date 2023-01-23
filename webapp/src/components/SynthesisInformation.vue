<template>
  <div id="synthesis-information">
    <label class="mr-2 pb-2">Synthesis Information</label>
    <table class="table mb-2">
      <thead>
        <tr class="subheading">
          <th>Component</th>
          <th>Formula</th>
          <th>Amount (g)</th>
        </tr>
      </thead>
      <tbody class="borderless">
        <tr v-for="(constituent, index) in constituents" :key="index">
          <td class="first-column" style="width: calc(70% - 1rem)">
            <transition name="fade">
              <font-awesome-icon
                v-if="!selectShown[index]"
                :icon="['fas', 'search']"
                class="swap-constituent-icon"
                @click="turnOnRowSelect(index)"
              />
            </transition>
            <ItemSelect
              class="select-in-row"
              v-if="selectShown[index]"
              :ref="`select${index}`"
              v-model="selectedChangedConstituent"
              :clearable="false"
              @option:selected="swapConstituent($event, index)"
              @search:blur="selectShown[index] = false"
            />
            <FormattedItemName
              v-else
              :item_id="constituent.item.item_id"
              :itemType="constituent.item.type"
              :name="constituent.item.name"
              enableClick
              enableModifiedClick
              @dblclick="turnOnRowSelect(index)"
            />
          </td>
          <td style="width: 20%">
            <ChemicalFormula :formula="constituent.item?.chemform" />
          </td>

          <td style="width: 10%">
            <input v-model="constituent.quantity" />
          </td>
          <td style="width: 2rem">
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
        <tr>
          <ItemSelect v-model="selectedNewConstituent" @option:selected="addConstituent" />
        </tr>
      </tbody>
    </table>
    <span id="synthesis-procedure-label" class="subheading ml-2">Procedure</span>
    <TinyMceInline
      aria-labelledby="synthesis-procedure-label"
      v-model="SynthesisDescription"
    ></TinyMceInline>
  </div>
</template>

<script>
import TinyMceInline from "@/components/TinyMceInline";
import ChemicalFormula from "@/components/ChemicalFormula.vue";
import { createComputedSetterForItemField } from "@/field_utils.js";

import ItemSelect from "@/components/ItemSelect.vue";
import FormattedItemName from "@/components/FormattedItemName.vue";

export default {
  components: {
    TinyMceInline,
    ChemicalFormula,
    ItemSelect,
    FormattedItemName,
  },
  data() {
    return {
      selectedNewConstituent: null,
      selectedChangedConstituent: null,
      selectShown: [],
    };
  },
  props: {
    item_id: String,
  },
  computed: {
    constituents: createComputedSetterForItemField("synthesis_constituents"),
    SynthesisDescription: createComputedSetterForItemField("synthesis_description"),
  },
  methods: {
    addConstituent(selectedItem) {
      this.constituents.push({
        item: selectedItem,
        quantity: null,
      });
      this.selectedNewConstituent = null;
      this.selectShown.push(false);
    },
    turnOnRowSelect(index) {
      this.selectShown[index] = true;
      this.selectedChangedConstituent = this.constituents[index].item;
      this.$nextTick(function () {
        // unfortunately this seems to be the "official" way to focus on the select element:
        this.$refs[`select${index}`].$refs.selectComponent.$refs.search.focus();
      });
    },
    swapConstituent(selectedItem, index) {
      this.constituents[index].item = selectedItem;
      this.selectShown[index] = false;
    },
    removeConstituent(index) {
      this.constituents.splice(index, 1);
      this.selectShown.splice(index, 1);
    },
  },
  mounted() {
    this.selectShown = new Array(this.constituents.length).fill(false);
  },
};
</script>

<style scoped>
.first-column {
  position: relative;
}

.swap-constituent-icon {
  cursor: pointer;
  position: absolute;
  font-size: regular;
  color: #bbb;
  float: right;
  transform: translateY(30%);
  transition: transform 0.4s ease;
  width: 1.5rem;
  left: -1.5rem;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.select-in-row {
  width: 100%;
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

.empty-search {
  opacity: 0.5;
  font-style: italic;
}
</style>
