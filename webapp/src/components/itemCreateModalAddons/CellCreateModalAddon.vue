<template>
  <div class="row form-inline form-group">
    <label class="pl-3">(Optional) Cell components:</label>
    <div class="col-md-12 form-group form-row ml-2 mt-3">
      <label id="posConstituentsLabel" class="col-sm-3 text-right cell-component-label"
        >Pos. electrode:
      </label>
      <ItemSelect
        v-model="posElectrodeConstituents"
        aria-labelledby="posConstituentsLabel"
        multiple
        :types-to-query="['samples', 'starting_materials']"
        taggable
        class="col-sm-9"
      />
    </div>

    <div class="col-md-12 form-group form-row ml-2 mt-3">
      <label id="elyteConstituentsLabel" class="col-sm-3 text-right cell-component-label"
        >Electrolyte:
      </label>
      <ItemSelect
        v-model="electrolyteConstituents"
        aria-labelledby="elyteConstituentsLabel"
        multiple
        :types-to-query="['samples', 'starting_materials']"
        taggable
        class="col-sm-9"
      />
    </div>

    <div class="col-md-12 form-group form-row ml-2 mt-3">
      <label id="negConstituentsLabel" class="col-sm-3 text-right cell-component-label"
        >Neg. electrode:</label
      >
      <ItemSelect
        v-model="negElectrodeConstituents"
        aria-labelledby="negConstituentsLabel"
        multiple
        :types-to-query="['samples', 'starting_materials']"
        taggable
        class="col-sm-9"
      />
    </div>
  </div>
</template>

<script>
import ItemSelect from "@/components/ItemSelect.vue";

export default {
  components: {
    ItemSelect,
  },
  emits: ["startingDataCallback"],
  data() {
    return {
      posElectrodeConstituents: [],
      electrolyteConstituents: [],
      negElectrodeConstituents: [],
    };
  },
  mounted() {
    this.$emit("startingDataCallback", this.createStartingConstituentsCallback);
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
};
</script>

<style scoped>
.cell-component-label {
  font-size: 0.95rem;
  justify-content: end;
}
</style>
