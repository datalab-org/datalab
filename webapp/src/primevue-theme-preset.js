import Aura from "@primevue/themes/aura";
import { definePreset } from "@primevue/themes";

const DatalabPreset = definePreset(Aura, {
  semantic: {
    transitionDuration: "0.05s",
  },
  components: {
    datatable: {
      extend: {
        filterActiveBackground: "{primary.50}",
        filterActiveColor: "{primary.700}",
        maxWidth: "1rem",
        whitespace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis",
      },
      bodyCellPadding: "0.4rem",
      sortIconColor: "transparent",
    },
    checkbox: {
      checkedBackground: "#fff",
      checkedBorderColor: "#ccc",
      iconCheckedColor: "#ccc",
      checkedHoverBackground: "#ccc",
      checkedHoverBorderColor: "#fff",
      iconCheckedHoverColor: "#fff",
    },
    button: {
      extend: {
        activeSVG: "{primary.700}",
      },
    },
  },
  css: ({ dt }) => `
        .p-datatable-thead tr th.filter-active {
          background: ${dt("datatable.filterActiveBackground")};
          color: ${dt("datatable.filterActiveColor")}
        }
        th.filter-active .p-button-text.p-button-secondary {
          color: ${dt("datatable.activeSVG")};
        }
        .p-datatable-tbody tr td {
          max-width: ${dt("datatable.maxWidth")};
          white-space: ${dt("datatable.whitespace")};
          overflow: ${dt("datatable.overflow")};
          text-overflow: ${dt("datatable.textOverflow")};
s        }
      `,
});

export default {
  preset: DatalabPreset,
  options: {
    darkModeSelector: "none",
  },
};
