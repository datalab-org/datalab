<template>
	<span class="badge badge-pill badge-warning text-uppercase">
			{{ status }}
  </span>
</template>

<script>

export default {
  props: {
    status: { type: String, required: true },
	}
};
</script>
