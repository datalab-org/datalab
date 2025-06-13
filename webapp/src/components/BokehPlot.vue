<template>
  <div v-if="loading" class="alert alert-secondary mt-3">Setting up bokeh plot...</div>
  <div :id="unique_id" ref="bokehPlotContainer" class="bokeh-plot-container" />
</template>

<script>
import * as Bokeh from "bokeh";

export default {
  name: "BokehPlot",
  props: {
    bokehPlotData: {
      type: Object,
      required: true,
      validator(value) {
        return (
          value &&
          typeof value.script === "string" &&
          (typeof value.html === "string" || typeof value.div === "string")
        );
      },
    },
  },
  data() {
    return {
      unique_id: "",
      loading: false,
    };
  },
  watch: {
    bokehPlotData: {
      handler() {
        this.updatePlot();
      },
      deep: true,
    },
  },
  mounted() {
    this.unique_id = this.guidGenerator();
    this.$nextTick(() => {
      this.renderPlot();
    });
  },
  beforeUnmount() {
    this.cleanup();
  },
  methods: {
    async renderPlot() {
      const htmlContent = this.bokehPlotData?.html || this.bokehPlotData?.div;
      const scriptContent = this.bokehPlotData?.script;

      if (!htmlContent || !scriptContent) {
        console.warn("BokehPlot: Invalid plot data provided");
        return;
      }

      this.loading = true;

      try {
        await this.injectPlot();
        this.applyCustomStyles();
        this.loading = false;
      } catch (error) {
        console.error("Error rendering Bokeh plot:", error);
        this.loading = false;
      }
    },

    async updatePlot() {
      this.cleanup();
      await this.renderPlot();
    },

    async injectPlot() {
      const container = this.$refs.bokehPlotContainer;
      if (!container) return;

      const htmlContent = this.bokehPlotData.html || this.bokehPlotData.div;
      container.innerHTML = htmlContent;

      await this.executeScript(this.bokehPlotData.script);
    },

    executeScript(scriptContent) {
      return new Promise((resolve, reject) => {
        try {
          let jsCode = scriptContent;
          if (scriptContent.includes("<script")) {
            const scriptMatch = scriptContent.match(/<script[^>]*>([\s\S]*?)<\/script>/);
            if (scriptMatch && scriptMatch[1]) {
              jsCode = scriptMatch[1];
            }
          }

          eval(jsCode);
          resolve();
        } catch (error) {
          reject(error);
        }
      });
    },

    applyCustomStyles() {
      const container = this.$refs.bokehPlotContainer;
      if (!container) return;

      const selectElements = container.querySelectorAll("div.bk-input-group > select");
      selectElements?.forEach((element) => {
        element.classList.add("form-control", "ml-4");
        element.classList.remove("bk-input", "bk");
      });

      const labelElements = container.querySelectorAll("div.bk-input-group > label");
      labelElements?.forEach((element) => {
        element.classList.remove("bk");
      });

      const inputGroups = container.querySelectorAll("div.bk-input-group");
      inputGroups?.forEach((element) => {
        element.classList.add("input-group", "form-inline", "col-sm-6");
        element.classList.remove("bk-input-group", "bk");
      });
    },

    cleanup() {
      const container = this.$refs.bokehPlotContainer;
      if (container) {
        console.log("Cleaning up Bokeh plot");

        const bokehElements = container.querySelectorAll("[data-root-id]");
        bokehElements.forEach((element) => {
          const rootId = element.getAttribute("data-root-id");
          if (rootId && Bokeh.documents) {
            try {
              delete Bokeh.documents[rootId];
            } catch (e) {
              console.log("Error: " + e);
            }
          }
        });

        container.innerHTML = "";
      }
    },
    guidGenerator() {
      var S4 = function () {
        return (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1);
      };
      return S4() + S4() + "-" + S4();
    },
  },
};
</script>

<style scoped>
.bokeh-plot-container {
  width: 100%;
  margin: 0 auto;
  display: flex;
  justify-content: center;
  max-width: 75%;
}
</style>
