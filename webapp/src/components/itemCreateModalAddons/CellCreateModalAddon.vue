<template>
  <div class="row form-inline">
    <label class="pl-3">(Optional) Cell components:</label>
    <div class="col-md-12 form-group form-row ml-2 mt-3">
      <label class="col-sm-3 text-right cell-component-label" id="posConstituentsLabel"
        >Pos. electrode:
      </label>
      <ItemSelect
        aria-labelledby="posConstituentsLabel"
        multiple
        v-model="posElectrodeConstituents"
        :typesToQuery='["samples", "starting_materials"]'
        taggable
        class="col-sm-9"
      />
    </div>

    <div class="col-md-12 form-group form-row ml-2 mt-3">
      <label class="col-sm-3 text-right cell-component-label" id="elyteConstituentsLabel"
        >Electrolyte:
      </label>
      <ItemSelect
        aria-labelledby="elyteConstituentsLabel"
        multiple
        v-model="electrolyteConstituents"
        :typesToQuery='["samples", "starting_materials"]'
        taggable
        class="col-sm-9"
      />
    </div>

    <div class="col-md-12 form-group form-row ml-2 mt-3">
      <label class="col-sm-3 text-right cell-component-label" id="negConstituentsLabel"
        >Neg. electrode:</label
      >
      <ItemSelect
        aria-labelledby="negConstituentsLabel"
        multiple
        v-model="negElectrodeConstituents"
        :typesToQuery='["samples", "starting_materials"]'
        taggable
        class="col-sm-9"
      />
    </div>
  </div>
</template>

<script>
import ItemSelect from "@/components/ItemSelect.vue";

export default {
  emits: ["startingDataCallback"],
  data() {
    return {
      posElectrodeConstituents: [],
      electrolyteConstituents: [],
      negElectrodeConstituents: [],
    };
  },
  methods: {
    createStartingConstituentsCallback() {
      const posElectrode = this.posElectrodeConstituents.map((x) => ({
        item: x,
        quantity: null,
      }));

      const electrolyte = this.electrolyteConstituents.map((x) => ({
        item: x,
        quantity: null,
      }));

      const negElectrode = this.negElectrodeConstituents.map((x) => ({
        item: x,
        quantity: null,
      }));

      console.log("the extra data is:");
      console.log({
        positive_electrode: posElectrode,
        electrolyte: electrolyte,
        negative_electrode: negElectrode,
      });

      return {
        positive_electrode: posElectrode,
        electrolyte: electrolyte,
        negative_electrode: negElectrode,
      };
    },
  },
  mounted() {
    this.$emit("startingDataCallback", this.createStartingConstituentsCallback);
  },
  components: {
    ItemSelect,
  },
};
</script>

<style scoped>
.cell-component-label {
  font-size: 0.95rem;
  justify-content: end;
}
</style>
