<template>
  <label :for="id">{{ Label }}</label>
  <input :id="id" type="text" />
</template>

<script>
export default {
  props: {
    inputId: { type: String, required: true },
  },
};
</script>
