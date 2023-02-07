<template>
  <div id="cell-preparation-information">
    <label class="mr-2 pb-2">Cell Construction</label>
    <table class="table table-sm mb-2" style="width: 80%; margin-left: 15%">
      <thead>
        <tr class="subheading">
          <th style="width: calc(60% - 7rem)">Component</th>
          <th style="width: 21%">Formula</th>
          <th style="width: 12%">Amount</th>
          <th style="width: 7%">Unit</th>
          <th style="width: 1rem"></th>
        </tr>
      </thead>
      <tbody class="borderless">
        <tr v-for="(constituent, index) in PosElectrodeConstituents" :key="index">
          <td class="first-column">
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
          <td>
            <ChemicalFormula :formula="constituent.item?.chemform" />
          </td>
          <td>
            <input
              class="form-control quantity-input"
              :class="{ 'red-border': isNaN(constituent.quantity) }"
              v-model="constituent.quantity"
            />
          </td>
          <td>
            <input class="form-control" v-model="constituent.unit" />
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
        <tr>
          <ItemSelect v-model="selectedNewConstituent" @option:selected="addConstituent" />
        </tr>
      </tbody>
    </table>
    <span id="synthesis-procedure-label" class="subheading ml-2">Procedure</span>
    <TinyMceInline
      aria-labelledby="synthesis-procedure-label"
      v-model="CellPreparationDescription"
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
    PosElectrodeConstituents: createComputedSetterForItemField("positive_electrode"),
    CellPreparationDescription: createComputedSetterForItemField("cell_preparation_description"),
  },
  methods: {
    addConstituent(selectedItem) {
      this.PosElectrodeConstituents.push({
        item: selectedItem,
        quantity: null,
        unit: "g",
      });
      this.selectedNewConstituent = null;
      this.selectShown.push(false);
    },
    turnOnRowSelect(index) {
      this.selectShown[index] = true;
      this.selectedChangedConstituent = this.PosElectrodeConstituents[index].item;
      this.$nextTick(function () {
        // unfortunately this seems to be the "official" way to focus on the select element:
        this.$refs[`select${index}`].$refs.selectComponent.$refs.search.focus();
      });
    },
    swapConstituent(selectedItem, index) {
      this.PosElectrodeConstituents[index].item = selectedItem;
      this.selectShown[index] = false;
    },
    removeConstituent(index) {
      this.PosElectrodeConstituents.splice(index, 1);
      this.selectShown.splice(index, 1);
    },
  },
  watch: {
    // since PosElectrodeConstituents is an object, the computed setter never fires and
    // saved status is never updated. So, use a watcher:
    PosElectrodeConstituents: {
      handler() {
        this.$store.commit("setSaved", { item_id: this.item_id, isSaved: false });
      },
      deep: true,
    },
  },
  mounted() {
    this.selectShown = new Array(this.PosElectrodeConstituents.length).fill(false);
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
