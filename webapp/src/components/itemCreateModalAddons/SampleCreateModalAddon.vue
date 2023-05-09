<template>
  <div class="row">
    <div class="col-md-12 form-group">
      <label id="startWithConstituentsLabel">(Optional) Start with constituents:</label>
      <ItemSelect
        aria-labelledby="startWithConstituentsLabel"
        multiple
        taggable
        v-model="constituents"
      />
    </div>
  </div>
</template>

<script>
import ItemSelect from "@/components/ItemSelect.vue";

export default {
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
  mounted() {
    this.initialConstituents && (this.constituents = this.initialconstituents);
    this.$emit("startingDataCallback", this.createStartingConstituentsCallback);
  },
  components: {
    ItemSelect,
  },
};
</script>
