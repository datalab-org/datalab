<template>
  <table style="width: 600px" class="table table-sm borderless">
    <colgroup>
      <col span="1" style="width: 300px" />
      <col span="1" style="width: 75px" />
      <col span="1" style="width: 50px" />
      <col span="1" style="width: 25px" />
    </colgroup>
    <tbody>
      <tr v-for="(constituent, index) in constituents" :key="index">
        <td>
          <!-- <transition name="fade"> -->
          <!--             <font-awesome-icon
              v-if="!selectShown[index]"
              :icon="['fas', 'search']"
              class="swap-constituent-icon"
              @click="turnOnRowSelect(index)"
            /> -->
          <!-- </transition> -->
          <ItemSelect
            v-if="selectShown[index]"
            :ref="`select${index}`"
            v-model="selectedChangedConstituent"
            class="select-in-row"
            :clearable="false"
            :types-to-query="typesToQuery"
            @option:selected="swapConstituent($event, index)"
            @search:blur="selectShown[index] = false"
          />
          <FormattedItemName
            v-else
            :item_id="constituent.item.item_id"
            :item-type="constituent.item.type"
            :name="constituent.item.name"
            :chemform="constituent.item.chemform || ''"
            enable-click
            enable-modified-click
            @dblclick="turnOnRowSelect(index)"
          />
        </td>
        <!--         <td>
          <ChemicalFormula :formula="constituent.item?.chemform" />
        </td> -->
        <td>
          <input
            v-model="constituent.quantity"
            class="form-control form-control-sm quantity-input"
            :class="{ 'red-border': isNaN(constituent.quantity) }"
            placeholder="quantity"
          />
        </td>
        <td>
          <input
            v-model="constituent.unit"
            class="form-control form-control-sm"
            placeholder="unit"
          />
        </td>

        <td>
          <button
            type="button"
            class="close"
            aria-label="delete"
            @click.stop="removeConstituent(index)"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </td>
      </tr>
      <tr>
        <td
          class="first-column"
          :class="{ clickable: !newSelectIsShown }"
          @click="
            addNewConstituentIsActive = true;
            focusNewSelect();
          "
        >
          <transition name="fade">
            <font-awesome-icon
              v-if="!newSelectIsShown"
              class="add-row-button clickable"
              :icon="['far', 'plus-square']"
            />
          </transition>
          <span v-if="!newSelectIsShown">&nbsp;</span>
          <OnClickOutside v-if="newSelectIsShown" @trigger="addNewConstituentIsActive = false">
            <ItemSelect
              ref="newSelect"
              v-model="selectedNewConstituent"
              taggable
              :types-to-query="typesToQuery"
              @option:selected="addConstituent"
            />
          </OnClickOutside>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import ItemSelect from "@/components/ItemSelect";
import FormattedItemName from "@/components/FormattedItemName.vue";
import { OnClickOutside } from "@vueuse/components";

export default {
  components: {
    ItemSelect,
    FormattedItemName,
    OnClickOutside,
  },
  props: {
    modelValue: {
      type: String,
      default: "",
    },
    typesToQuery: {
      type: Array,
      default: () => ["samples", "starting_materials", "cells"],
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      selectedNewConstituent: null,
      selectedChangedConstituent: null,
      selectShown: [],
      addNewConstituentIsActive: false,
    };
  },
  computed: {
    newSelectIsShown() {
      return this.constituents.length == 0 || this.addNewConstituentIsActive;
    },
    constituents: {
      get() {
        if (!this.modelValue) {
          return [];
        }
        return this.modelValue;
      },
      set(value) {
        this.$emit("update:modelValue", value);
      },
    },
  },
  methods: {
    addConstituent(selectedItem) {
      this.constituents.push({
        item: selectedItem,
        quantity: null,
        unit: "g",
      });
      this.selectedNewConstituent = null;
      this.selectShown.push(false);
      this.addNewConstituentIsActive = false;
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
    focusNewSelect() {
      this.$nextTick(() => {
        this.$refs["newSelect"].$refs.selectComponent.$refs.search.focus();
      });
    },
  },
};
</script>

<style scoped>
td {
  padding: 0.2rem !important;
}

.first-column {
  position: relative;
}

.add-row-button {
  position: absolute;
  font-size: regular;
  color: #bbb;
  float: right;
  transform: translateY(-50%);
  transition: transform 0.4s ease;
  width: 1.5rem;
  left: -2rem;
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

.borderless tr,
.borderless td {
  border: none !important;
}
</style>
