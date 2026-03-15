<template>
  <div v-if="info" class="deployment-info">
    <div class="info-grid">
      <div class="info-card">
        <div class="info-label">API version</div>
        <div class="info-value">
          <code>{{ info.server_version ?? "unknown" }}</code>
        </div>
      </div>
      <div class="info-card">
        <div class="info-label">App version</div>
        <div class="info-value">
          <code>{{ appVersion }}</code>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getInfo } from "@/server_fetch_utils.js";
import { APP_VERSION } from "@/resources.js";

export default {
  data() {
    return {
      info: null,
      appVersion: APP_VERSION,
    };
  },
  async mounted() {
    this.info = this.$store.state.serverInfo;
    if (!this.info) {
      this.info = await getInfo();
    }
  },
};
</script>

<style scoped>
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.info-card {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 12px;
  text-align: center;
}

.info-label {
  font-size: 0.75em;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #6c757d;
  margin-bottom: 4px;
  font-weight: 600;
}

.info-value code {
  font-size: 0.85em;
  color: #212529;
}
</style>
