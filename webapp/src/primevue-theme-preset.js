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
        minWidth: "1rem",
        maxWidth: "10rem",
        whitespace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis",
        divCheckboxHover: "#6C757D",
        divCheckboxCheckedHover: "#5A6268",
        dropdownDisplay: "none",
      },
      bodyCellPadding: "0.4rem",
      sortIconColor: "transparent",
    },
    checkbox: {
      hoverBorderColor: "#6C757D",
      checkedBackground: "#6C757D",
      checkedBorderColor: "#6C757D",
      iconCheckedColor: "#F8F9FA",
      checkedHoverBackground: "#5A6268",
      checkedHoverBorderColor: "#5A6268",
      iconCheckedHoverColor: "#F8F9FA",
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
          min-width: ${dt("datatable.minWidth")};
          max-width: ${dt("datatable.maxWidth")};
          white-space: ${dt("datatable.whitespace")};
          overflow: ${dt("datatable.overflow")};
          text-overflow: ${dt("datatable.textOverflow")};
        }
        .checkbox:hover .p-checkbox-box {
          border-color: ${dt("datatable.divCheckboxHover")};
        }
        .checkbox:hover .p-checkbox-checked .p-checkbox-box {
          border-color: ${dt("datatable.divCheckboxCheckedHover")};
          background: ${dt("datatable.divCheckboxCheckedHover")};
        }
        .p-datatable-filter-constraint-dropdown {
          display: none !important;
        }
        .p-datatable-filter-remove-rule-button {
          display: none !important;
        }
        .p-datatable-filter-add-rule-button {
          display: none !important;
        }
        .no-operator .p-datatable-filter-operator {
          display: none !important;
        }
        .p-datatable-sortable-column.hide-single-sort-badge .p-datatable-sort-badge {
          display: none;
        }
        .p-multiselect-header .p-checkbox::after {
          content: 'Select all';
          position: absolute;
          left: 28px;
          width: 110px;
        }
        .p-datatable-mask {
          color: black;
          background: none;
        }
      `,
});

export default {
  preset: DatalabPreset,
  options: {
    darkModeSelector: "none",
  },
};
