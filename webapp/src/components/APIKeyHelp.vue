<template>
  <div class="api-key-help mb-2">
    <button
      class="btn btn-link btn-sm p-0 api-key-help-toggle"
      type="button"
      :aria-expanded="expanded"
      @click="expanded = !expanded"
    >
      <font-awesome-icon icon="question-circle" class="mr-1" />
      How do I use an API key?
      <font-awesome-icon
        icon="chevron-right"
        :rotation="expanded ? 90 : undefined"
        class="ml-1 api-key-help-chevron"
      />
    </button>

    <div v-if="expanded" class="card card-body mt-2 small api-key-help-card">
      <p>
        API keys let scripts and other tools access <i>datalab</i> on your behalf, without logging
        in through the browser. Anything you can do in the web interface can be done with a key, so
        treat it like a password: do not share it or commit it to version control. If a key is
        exposed, delete it here and generate a new one.
      </p>

      <p class="mb-1"><strong>Potential uses:</strong></p>
      <ul>
        <li>Searching and downloading your samples, cells and data for analysis in notebooks.</li>
        <li>Bulk-creating items or uploading files directly from instruments or scripts.</li>
        <li>Automating workflows, e.g., syncing with other databases or running in CI.</li>
      </ul>

      <ul class="nav nav-tabs mb-2" role="tablist" aria-label="API key examples">
        <li v-for="tab in tabs" :key="tab.id" class="nav-item" role="presentation">
          <button
            :id="`api-key-example-tab-${tab.id}`"
            ref="tabButtons"
            class="nav-link"
            :class="{ active: activeTab === tab.id }"
            type="button"
            role="tab"
            :aria-selected="activeTab === tab.id"
            aria-controls="api-key-example-panel"
            :tabindex="activeTab === tab.id ? 0 : -1"
            @click="activeTab = tab.id"
            @keydown.left.prevent="moveTabFocus(-1)"
            @keydown.right.prevent="moveTabFocus(1)"
          >
            {{ tab.label }}
          </button>
        </li>
      </ul>

      <div
        id="api-key-example-panel"
        role="tabpanel"
        :aria-labelledby="`api-key-example-tab-${activeTab}`"
        tabindex="0"
      >
        <p v-if="activeTab === 'python'">
          The
          <a href="https://github.com/datalab-org/datalab-api" target="_blank">datalab-api</a>
          Python package (<code>pip install datalab-api</code>) reads your key from the
          <code>DATALAB_API_KEY</code> environment variable. To list your samples:
        </p>
        <p v-else>
          Pass the key in the <code>DATALAB-API-KEY</code> HTTP header with any HTTP client, e.g.,
          <code>curl</code>. To list your samples:
        </p>

        <div class="api-key-help-code-wrapper">
          <pre class="api-key-help-code"><code>{{ currentExample }}</code></pre>
          <button
            class="btn btn-sm btn-outline-secondary api-key-help-copy"
            type="button"
            :title="copied ? 'Copied!' : 'Copy to clipboard'"
            @click="copyExample"
          >
            <font-awesome-icon :icon="copied ? 'check' : 'copy'" />
          </button>
        </div>
      </div>

      <p class="mt-2 mb-0">
        For more details, see the
        <a href="https://guide.datalab-org.io/api/" target="_blank">user guide</a>
        and the
        <a href="https://api-docs.datalab-org.io/en/stable/" target="_blank">API documentation</a>.
      </p>
    </div>
  </div>
</template>

<script>
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { API_URL } from "@/resources.js";

export default {
  name: "APIKeyHelp",
  components: { FontAwesomeIcon },
  data() {
    return {
      expanded: false,
      activeTab: "python",
      copied: false,
      tabs: [
        { id: "python", label: "Python" },
        { id: "curl", label: "curl" },
      ],
    };
  },
  computed: {
    examples() {
      return {
        python: `# export DATALAB_API_KEY=<your key>
from datalab_api import DatalabClient

with DatalabClient("${API_URL}") as client:
    samples = client.get_items("samples")`,
        curl: `export DATALAB_API_KEY=<your key>

curl -H "DATALAB-API-KEY: $DATALAB_API_KEY" \\
  ${API_URL}/samples/`,
      };
    },
    currentExample() {
      return this.examples[this.activeTab];
    },
  },
  watch: {
    activeTab() {
      this.copied = false;
    },
  },
  methods: {
    moveTabFocus(offset) {
      const current = this.tabs.findIndex((tab) => tab.id === this.activeTab);
      const index = (current + offset + this.tabs.length) % this.tabs.length;
      this.activeTab = this.tabs[index].id;
      this.$nextTick(() => this.$refs.tabButtons?.[index]?.focus());
    },
    async copyExample() {
      await navigator.clipboard.writeText(this.currentExample);
      this.copied = true;
      setTimeout(() => {
        this.copied = false;
      }, 2000);
    },
  },
};
</script>

<style scoped>
.api-key-help-toggle {
  color: #6c757d;
  text-decoration: none;
}

.api-key-help-toggle:hover,
.api-key-help-toggle:focus {
  color: #0056b3;
  text-decoration: none;
}

.api-key-help-chevron {
  font-size: 0.7em;
}

.api-key-help-card {
  background-color: #faf8f5;
  border-color: #ebe3d2;
}

.api-key-help-card .nav-tabs {
  border-bottom-color: #ebe3d2;
}

.api-key-help-card .nav-tabs .nav-link {
  background-color: transparent;
}

.api-key-help-card .nav-tabs .nav-link.active {
  background-color: #faf8f5;
  border-color: #ebe3d2 #ebe3d2 #faf8f5;
}

.api-key-help-code-wrapper {
  position: relative;
}

.api-key-help-code {
  background-color: #f4efe3;
  border: 1px solid #e3d9c4;
  border-radius: 0.25rem;
  padding: 0.5rem 2.75rem 0.5rem 0.5rem;
  margin-bottom: 0;
  white-space: pre;
  overflow-x: auto;
}

.api-key-help-copy {
  position: absolute;
  top: 0.35rem;
  right: 0.35rem;
  background-color: white;
}
</style>
