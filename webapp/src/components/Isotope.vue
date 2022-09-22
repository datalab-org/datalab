<template>
  <span v-if="isotopeString">
    <sup>{{ isotopeFormat[1] }}</sup
    >{{ isotopeFormat[2] }}
  </span>
  <!-- <span v-else><i>no isotope found</i></span> -->
</template>

<script>
export default {
  props: { isotopeString: String },
  computed: {
    isotopeFormat() {
      const re = /(\d+)([A-z][a-z]?)/;
      var match = this.isotopeString.match(re);
      return match ? match : [null, null, this.isotopeString];
    },
  },
};
</script>
