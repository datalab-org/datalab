<template>
  <div class="row">
    <div class="col-md-12 form-group">
      <label id="startWithConstituentsLabel">(Optional) Start with constituents:</label>
      <ItemSelect
        v-model="constituents"
        aria-labelledby="startWithConstituentsLabel"
        multiple
        :types-to-query="['samples', 'starting_materials']"
        taggable
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
  props: {
    initialConstituents: {
      type: Array,
      default: null,
    },
  },
  emits: ["startingDataCallback"],
  data() {
    return {
      constituents: [],
    };
  },
  mounted() {
    this.initialConstituents && (this.constituents = this.initialconstituents);
    this.$emit("startingDataCallback", this.createStartingConstituentsCallback);
  },
  methods: {
    createStartingConstituentsCallback() {
      const startingSynthesisBlock = this.constituents.map((x) => ({
        item: x,
        quantity: null,
      }));

      return {
        synthesis_constituents: startingSynthesisBlock,
      };
    },
  },
};
</script>
