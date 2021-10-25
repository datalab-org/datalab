<template>
  <ChemicalFormula
    v-show="!editable"
    class="form-control"
    :formula="internal_chemform"
    @click="handleSpanClick"
  />
  <input
    v-show="editable"
    @blur="editable = false"
    ref="input"
    @keyup.enter="$refs['input'].blur()"
    class="form-control"
    v-model="internal_chemform"
  />
</template>

<script>
import ChemicalFormula from "@/components/ChemicalFormula";
export default {
  data() {
    return {
      editable: false,
    };
  },
  props: { modelValue: String },
  methods: {
    chemFormulaFormat(chemform) {
      if (!chemform) {
        return " ";
      }
      var re = /([\d.]+)/g;
      return chemform.replace(re, "<sub>$1</sub>");
    },
    handleSpanClick() {
      this.editable = true; // triggers the span to dissappear and the click to appear
      this.$nextTick(function () {
        // wait for the dom to update (i.e. wait for the input to appear) and then focus the input
        // Note: I tried for a while to get the cursor to go to the clicked position by passing the original click
        // coordinates to a new MouseEvent or FocusEvent, but couldn't make it work. So, for now this puts the cursor
        // at the end of the formula
        this.$refs["input"].focus();
      });
    },
  },
  computed: {
    internal_chemform: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit("update:modelValue", value);
      },
    },
  },
  components: {
    ChemicalFormula,
  },
};
</script>
