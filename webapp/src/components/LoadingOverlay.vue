<template>
  <div
    class="position-fixed d-flex justify-content-center align-items-center"
    style="background-color: rgba(255, 255, 255, 0.7); z-index: 1050; inset: 0"
  >
    <div class="card p-3 shadow-sm">
      <div class="text-center">
        <font-awesome-icon
          :icon="['fa', 'sync']"
          class="fa-2x text-primary mb-2"
          :spin="true"
          aria-label="loading"
        />
        <p class="mb-0 mt-1"><slot /></p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "LoadingOverlay",
};
</script>
