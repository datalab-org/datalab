<template>
  <div class="row">
    <label>(Optional) Cell components:</label>
    <div class="col-md-12 row mt-3">
      <label
        id="posConstituentsLabel"
        class="d-flex justify-content-end col-sm-4 text-end cell-component-label"
        >Pos. electrode:
      </label>
      <ItemSelect
        v-model="posElectrodeConstituents"
        aria-labelledby="posConstituentsLabel"
        multiple
        :types-to-query="['samples', 'starting_materials']"
        taggable
        class="col-sm-8"
      />
    </div>

    <div class="col-md-12 row mt-3">
      <label
        id="elyteConstituentsLabel"
        class="d-flex justify-content-end col-sm-4 text-end cell-component-label"
        >Electrolyte:
      </label>
      <ItemSelect
        v-model="electrolyteConstituents"
        aria-labelledby="elyteConstituentsLabel"
        multiple
        :types-to-query="['samples', 'starting_materials']"
        taggable
        class="col-sm-8"
      />
    </div>

    <div class="col-md-12 row mt-3">
      <label
        id="negConstituentsLabel"
        class="d-flex justify-content-end col-sm-4 text-end cell-component-label"
        >Neg. electrode:</label
      >
      <ItemSelect
        v-model="negElectrodeConstituents"
        aria-labelledby="negConstituentsLabel"
        multiple
        :types-to-query="['samples', 'starting_materials']"
        taggable
        class="col-sm-8"
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
  align-items: center;
  font-size: 0.95rem;
}
</style>
