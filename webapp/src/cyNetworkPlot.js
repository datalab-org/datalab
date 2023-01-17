import cytoscape from "cytoscape";
import dagre from "cytoscape-dagre";
import cola from "cytoscape-cola";
import klay from "cytoscape-klay";

cytoscape.use(dagre);
cytoscape.use(cola);
cytoscape.use(klay);

export function cyNetworkPlot() {
  var graphData = {
    nodes: [
      { data: { id: "AB000542", name: "Kynar HSV 900 PVDF monomer", type: "starting_materials" } },
      {
        data: { id: "ABJ00302", name: "Kynar HSV 900, PVDF (monomer)", type: "starting_materials" },
      },
      { data: { id: "AB000049", name: "Manganese(II) oxide", type: "starting_materials" } },
      { data: { id: "AB000059", name: "Manganese(II) oxide", type: "starting_materials" } },
      { data: { id: "AB000204", name: "N-Methyl-2-pyrrolidone", type: "starting_materials" } },
      { data: { id: "ABJ00532", name: "Nickel Oxide", type: "starting_materials" } },
      { data: { id: "ABJ00044", name: "Nickel(II) Oxide", type: "starting_materials" } },
      { data: { id: "AB000192", name: "Sodium carbonate", type: "starting_materials" } },
      { data: { id: "AB000194", name: "Sodium carbonate", type: "starting_materials" } },
      { data: { id: "ABJ00190", name: "Super P", type: "starting_materials" } },
      { data: { id: "AB000318", name: "Titanium (IV) oxide, rutile", type: "starting_materials" } },
      { data: { id: "jmas-1-1", name: "NaNiO2", type: "samples" } },
      { data: { id: "jmas-2-1", name: "NaNi0.5Mn0.5O2", type: "samples" } },
      { data: { id: "jmas-1-2", name: "NaNiO2", type: "samples" } },
      { data: { id: "jmas-2-2", name: "NaNi0.5Mn0.5O2", type: "samples" } },
      { data: { id: "jmas-1-4a", name: "NaNiO2 (5wt% excess Na2O2)", type: "samples" } },
      { data: { id: "jmas-1-4b", name: "NaNiO2 (10wt% excess Na2O2)", type: "samples" } },
      {
        data: {
          id: "jmas-1-4a-e1-c1",
          name: "NaNiO2 Electrode 1 Coin Cell 1 (C/10, 20 cycles, 1.25-3.75V)",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-1-4a-e1-c2",
          name: "NaNiO2 Electrode 1 Coin Cell 2 (C/10, 20 cycles, 1.25-3.75V)",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-1-4a-e1-c3",
          name: "NaNiO2 Electrode 1 Coin Cell 3 (C/10, 20 cycles, 2.0-4.5V)",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-3-2-e1-c1",
          name: "NaNi0.95Ti0.05O2 Electrode 1 Coin Cell 1 (C/10, 20 cycles, 1.25-3.75V)",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-3-2-e1-c2",
          name: "NaNi0.95Ti0.05O2 Electrode 1 Coin Cell 2 (C/10, 20 cycles, 1.25-3.75V)",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-3-2-e1-c3",
          name: "NaNi0.95Ti0.05O2 Electrode 1 Coin Cell 3 (C/10, 20 Cycles, 2-4.5V)",
          type: "samples",
        },
      },
      { data: { id: "jmas-1-4a-e1", name: "NaNiO2 Electrode", type: "samples" } },
      { data: { id: "jmas-3-2-e1", name: "NaNi0.95Ti0.05O2 Electrode", type: "samples" } },
      {
        data: {
          id: "jmas-1-4a-e1-c4",
          name: "jmas-1-4a-e1-c4_NaNiO2_Con10_2V-2p89V-charge-cutoff-data",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-1-4a-e1-c7",
          name: "jmas-1-4a-e1-c7_NaNiO2_Con10_2V-4p5V-2V-discharge-cutoff-data",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-3-2-e1-c4",
          name: "jmas-3-2-e1-c4_NaNi0p95Ti0p05O2_Con10_2V-2.89V_charge_cutoff-data",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-3-2-e1-c5",
          name: "jmas-3-2-e1-c5_NaNi0p95Ti0p05O2_Con10_2V-3p46V_charge_cutoff-data",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-3-2-e1-c6",
          name: "jmas-3-2-e1-c6_NaNi0p95Ti0p05O2_Con10_2V-4p5V_charge_cutoff-data",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-3-2-e1-c7",
          name: "jmas-3-2-e1-c7_NaNi0p95Ti0p05O2_Con10_2V-4p5V-2V-discharge-cutoff-data",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-1-4a-e1-c5",
          name: "jmas-1-4a-e1-c5_NaNiO2_Con10_2V-3p46V-charge-cutoff-data_C02",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-1-4a-e1-c6",
          name: "jmas-1-4a-e1-c6_NaNiO2_Con10_2V-4p5V-charge-cutoff-data_C09",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-3-1-e1-c1",
          name: "NaNi0.95Ti0.05O2 1 Coin Cell 1 (20 cycles, C/10, 1.25-3.75V)",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-3-1-e1-c2",
          name: "NaNi0.95Ti0.05O2 1 Coin Cell 2 (20 cycles, C/10, 1.25-3.75V)",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-3-1-e1-c3",
          name: "NaNi0.95Ti0.05O2 1 Coin Cell 3 (20 cycles, C/10, 2.0-4.5V)",
          type: "samples",
        },
      },
      {
        data: {
          id: "jmas-3-1-e1-c4",
          name: "NaNi0.95Ti0.05O2 1 Coin Cell 4 (20 cycles, C/10, 2.0-4.5V)",
          type: "samples",
        },
      },
      { data: { id: "jmas-3-1", name: "NaNi0.95Ti0.05O2", type: "samples" } },
      { data: { id: "jmas-1-3", name: "NaNiO2", type: "samples" } },
      { data: { id: "jmas-1-4c", name: "NaNiO2 (15wt% excess Na2O2)", type: "samples" } },
      { data: { id: "jmas-1-4d", name: "NaNiO2 (20wt% excess Na2O2)", type: "samples" } },
      { data: { id: "jmas-3-2", name: "NaNi0.95Ti0.05O2", type: "samples" } },
      {
        data: {
          id: "jmas-3-1-e1",
          name: "NaNi0.95Ti0.05O2 Electrode 1 (700oC Synthesis)",
          type: "samples",
        },
      },
    ],
    edges: [
      { data: { id: "ABJ00532->jmas-1-1", source: "ABJ00532", target: "jmas-1-1", value: 1 } },
      { data: { id: "AB000194->jmas-1-1", source: "AB000194", target: "jmas-1-1", value: 1 } },
      { data: { id: "AB000192->jmas-2-1", source: "AB000192", target: "jmas-2-1", value: 1 } },
      { data: { id: "ABJ00532->jmas-2-1", source: "ABJ00532", target: "jmas-2-1", value: 1 } },
      { data: { id: "AB000049->jmas-2-1", source: "AB000049", target: "jmas-2-1", value: 1 } },
      { data: { id: "ABJ00044->jmas-1-2", source: "ABJ00044", target: "jmas-1-2", value: 1 } },
      { data: { id: "ABJ00044->jmas-2-2", source: "ABJ00044", target: "jmas-2-2", value: 1 } },
      { data: { id: "AB000059->jmas-2-2", source: "AB000059", target: "jmas-2-2", value: 1 } },
      {
        data: {
          id: "jmas-1-4a-e1->jmas-1-4a-e1-c1",
          source: "jmas-1-4a-e1",
          target: "jmas-1-4a-e1-c1",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-1-4a-e1->jmas-1-4a-e1-c2",
          source: "jmas-1-4a-e1",
          target: "jmas-1-4a-e1-c2",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-1-4a-e1->jmas-1-4a-e1-c3",
          source: "jmas-1-4a-e1",
          target: "jmas-1-4a-e1-c3",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-3-2-e1->jmas-3-2-e1-c1",
          source: "jmas-3-2-e1",
          target: "jmas-3-2-e1-c1",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-3-2-e1->jmas-3-2-e1-c2",
          source: "jmas-3-2-e1",
          target: "jmas-3-2-e1-c2",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-3-2-e1->jmas-3-2-e1-c3",
          source: "jmas-3-2-e1",
          target: "jmas-3-2-e1-c3",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-1-4a->jmas-1-4a-e1",
          source: "jmas-1-4a",
          target: "jmas-1-4a-e1",
          value: 1,
        },
      },
      {
        data: {
          id: "ABJ00190->jmas-1-4a-e1",
          source: "ABJ00190",
          target: "jmas-1-4a-e1",
          value: 1,
        },
      },
      {
        data: {
          id: "AB000542->jmas-1-4a-e1",
          source: "AB000542",
          target: "jmas-1-4a-e1",
          value: 1,
        },
      },
      {
        data: {
          id: "AB000204->jmas-1-4a-e1",
          source: "AB000204",
          target: "jmas-1-4a-e1",
          value: 1,
        },
      },
      {
        data: { id: "ABJ00190->jmas-3-2-e1", source: "ABJ00190", target: "jmas-3-2-e1", value: 1 },
      },
      {
        data: { id: "ABJ00302->jmas-3-2-e1", source: "ABJ00302", target: "jmas-3-2-e1", value: 1 },
      },
      {
        data: { id: "AB000204->jmas-3-2-e1", source: "AB000204", target: "jmas-3-2-e1", value: 1 },
      },
      {
        data: { id: "jmas-3-2->jmas-3-2-e1", source: "jmas-3-2", target: "jmas-3-2-e1", value: 1 },
      },
      {
        data: {
          id: "jmas-1-4a-e1->jmas-1-4a-e1-c4",
          source: "jmas-1-4a-e1",
          target: "jmas-1-4a-e1-c4",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-1-4a-e1->jmas-1-4a-e1-c7",
          source: "jmas-1-4a-e1",
          target: "jmas-1-4a-e1-c7",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-3-2-e1->jmas-3-2-e1-c4",
          source: "jmas-3-2-e1",
          target: "jmas-3-2-e1-c4",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-3-2-e1->jmas-3-2-e1-c5",
          source: "jmas-3-2-e1",
          target: "jmas-3-2-e1-c5",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-3-2-e1->jmas-3-2-e1-c6",
          source: "jmas-3-2-e1",
          target: "jmas-3-2-e1-c6",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-3-2-e1->jmas-3-2-e1-c7",
          source: "jmas-3-2-e1",
          target: "jmas-3-2-e1-c7",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-1-4a-e1->jmas-1-4a-e1-c5",
          source: "jmas-1-4a-e1",
          target: "jmas-1-4a-e1-c5",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-1-4a-e1->jmas-1-4a-e1-c6",
          source: "jmas-1-4a-e1",
          target: "jmas-1-4a-e1-c6",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-3-1-e1->jmas-3-1-e1-c1",
          source: "jmas-3-1-e1",
          target: "jmas-3-1-e1-c1",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-3-1-e1->jmas-3-1-e1-c2",
          source: "jmas-3-1-e1",
          target: "jmas-3-1-e1-c2",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-3-1-e1->jmas-3-1-e1-c3",
          source: "jmas-3-1-e1",
          target: "jmas-3-1-e1-c3",
          value: 1,
        },
      },
      {
        data: {
          id: "jmas-3-1-e1->jmas-3-1-e1-c4",
          source: "jmas-3-1-e1",
          target: "jmas-3-1-e1-c4",
          value: 1,
        },
      },
      { data: { id: "ABJ00044->jmas-3-1", source: "ABJ00044", target: "jmas-3-1", value: 1 } },
      { data: { id: "AB000318->jmas-3-1", source: "AB000318", target: "jmas-3-1", value: 1 } },
      { data: { id: "ABJ00044->jmas-1-3", source: "ABJ00044", target: "jmas-1-3", value: 1 } },
      { data: { id: "AB000318->jmas-3-2", source: "AB000318", target: "jmas-3-2", value: 1 } },
      {
        data: { id: "ABJ00190->jmas-3-1-e1", source: "ABJ00190", target: "jmas-3-1-e1", value: 1 },
      },
      {
        data: { id: "ABJ00302->jmas-3-1-e1", source: "ABJ00302", target: "jmas-3-1-e1", value: 1 },
      },
      {
        data: { id: "AB000204->jmas-3-1-e1", source: "AB000204", target: "jmas-3-1-e1", value: 1 },
      },
      {
        data: { id: "jmas-3-1->jmas-3-1-e1", source: "jmas-3-1", target: "jmas-3-1-e1", value: 1 },
      },
    ],
  };
  // var graphDataold = {
  //   nodes: [
  //     { data: { id: "AB000542", name: "Kynar HSV 900 PVDF monomer", type: "starting_materials" } },
  //     {
  //       data: { id: "ABJ00302", name: "Kynar HSV 900, PVDF (monomer)", type: "starting_materials" },
  //     },
  //     { data: { id: "AB000049", name: "Manganese(II) oxide", type: "starting_materials" } },
  //     { data: { id: "AB000059", name: "Manganese(II) oxide", type: "starting_materials" } },
  //     { data: { id: "AB000204", name: "N-Methyl-2-pyrrolidone", type: "starting_materials" } },
  //     { data: { id: "ABJ00532", name: "Nickel Oxide", type: "starting_materials" } },
  //     { data: { id: "ABJ00044", name: "Nickel(II) Oxide", type: "starting_materials" } },
  //     { data: { id: "AB000192", name: "Sodium carbonate", type: "starting_materials" } },
  //     { data: { id: "AB000194", name: "Sodium carbonate", type: "starting_materials" } },
  //     { data: { id: "ABJ00190", name: "Super P", type: "starting_materials" } },
  //     { data: { id: "AB000318", name: "Titanium (IV) oxide, rutile", type: "starting_materials" } },
  //     { data: { id: "jmas-1-1", name: "NaNiO2", type: "samples" } },
  //     { data: { id: "jmas-2-1", name: "NaNi0.5Mn0.5O2", type: "samples" } },
  //     { data: { id: "jmas-1-2", name: "NaNiO2", type: "samples" } },
  //     { data: { id: "jmas-2-2", name: "NaNi0.5Mn0.5O2", type: "samples" } },
  //     { data: { id: "jmas-1-4a", name: "NaNiO2 (5wt% excess Na2O2)", type: "samples" } },
  //     { data: { id: "jmas-1-4b", name: "NaNiO2 (10wt% excess Na2O2)", type: "samples" } },
  //     {
  //       data: {
  //         id: "jmas-1-4a-e1-c1",
  //         name: "NaNiO2 Electrode 1 Coin Cell 1 (C/10, 20 cycles, 1.25-3.75V)",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-1-4a-e1-c2",
  //         name: "NaNiO2 Electrode 1 Coin Cell 2 (C/10, 20 cycles, 1.25-3.75V)",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-1-4a-e1-c3",
  //         name: "NaNiO2 Electrode 1 Coin Cell 3 (C/10, 20 cycles, 2.0-4.5V)",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-2-e1-c1",
  //         name: "NaNi0.95Ti0.05O2 Electrode 1 Coin Cell 1 (C/10, 20 cycles, 1.25-3.75V)",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-2-e1-c2",
  //         name: "NaNi0.95Ti0.05O2 Electrode 1 Coin Cell 2 (C/10, 20 cycles, 1.25-3.75V)",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-2-e1-c3",
  //         name: "NaNi0.95Ti0.05O2 Electrode 1 Coin Cell 3 (C/10, 20 Cycles, 2-4.5V)",
  //         type: "samples",
  //       },
  //     },
  //     { data: { id: "jmas-1-4a-e1", name: "NaNiO2 Electrode", type: "samples" } },
  //     { data: { id: "jmas-3-2-e1", name: "NaNi0.95Ti0.05O2 Electrode", type: "samples" } },
  //     {
  //       data: {
  //         id: "jmas-1-4a-e1-c4",
  //         name: "jmas-1-4a-e1-c4_NaNiO2_Con10_2V-2p89V-charge-cutoff-data",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-1-4a-e1-c7",
  //         name: "jmas-1-4a-e1-c7_NaNiO2_Con10_2V-4p5V-2V-discharge-cutoff-data",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-2-e1-c4",
  //         name: "jmas-3-2-e1-c4_NaNi0p95Ti0p05O2_Con10_2V-2.89V_charge_cutoff-data",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-2-e1-c5",
  //         name: "jmas-3-2-e1-c5_NaNi0p95Ti0p05O2_Con10_2V-3p46V_charge_cutoff-data",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-2-e1-c6",
  //         name: "jmas-3-2-e1-c6_NaNi0p95Ti0p05O2_Con10_2V-4p5V_charge_cutoff-data",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-2-e1-c7",
  //         name: "jmas-3-2-e1-c7_NaNi0p95Ti0p05O2_Con10_2V-4p5V-2V-discharge-cutoff-data",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-1-4a-e1-c5",
  //         name: "jmas-1-4a-e1-c5_NaNiO2_Con10_2V-3p46V-charge-cutoff-data_C02",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-1-4a-e1-c6",
  //         name: "jmas-1-4a-e1-c6_NaNiO2_Con10_2V-4p5V-charge-cutoff-data_C09",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-1-e1-c1",
  //         name: "NaNi0.95Ti0.05O2 1 Coin Cell 1 (20 cycles, C/10, 1.25-3.75V)",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-1-e1-c2",
  //         name: "NaNi0.95Ti0.05O2 1 Coin Cell 2 (20 cycles, C/10, 1.25-3.75V)",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-1-e1-c3",
  //         name: "NaNi0.95Ti0.05O2 1 Coin Cell 3 (20 cycles, C/10, 2.0-4.5V)",
  //         type: "samples",
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-1-e1-c4",
  //         name: "NaNi0.95Ti0.05O2 1 Coin Cell 4 (20 cycles, C/10, 2.0-4.5V)",
  //         type: "samples",
  //       },
  //     },
  //     { data: { id: "jmas-3-1", name: "NaNi0.95Ti0.05O2", type: "samples" } },
  //     { data: { id: "jmas-1-3", name: "NaNiO2", type: "samples" } },
  //     { data: { id: "jmas-1-4c", name: "NaNiO2 (15wt% excess Na2O2)", type: "samples" } },
  //     { data: { id: "jmas-1-4d", name: "NaNiO2 (20wt% excess Na2O2)", type: "samples" } },
  //     { data: { id: "jmas-3-2", name: "NaNi0.95Ti0.05O2", type: "samples" } },
  //     {
  //       data: {
  //         id: "jmas-3-1-e1",
  //         name: "NaNi0.95Ti0.05O2 Electrode 1 (700oC Synthesis)",
  //         type: "samples",
  //       },
  //     },
  //   ],
  //   edges: [
  //     { data: { id: "ABJ00532->jmas-1-1", source: "ABJ00532", target: "jmas-1-1", value: 1 } },
  //     { data: { id: "AB000194->jmas-1-1", source: "AB000194", target: "jmas-1-1", value: 1 } },
  //     { data: { id: "AB000192->jmas-2-1", source: "AB000192", target: "jmas-2-1", value: 1 } },
  //     { data: { id: "ABJ00532->jmas-2-1", source: "ABJ00532", target: "jmas-2-1", value: 1 } },
  //     { data: { id: "AB000049->jmas-2-1", source: "AB000049", target: "jmas-2-1", value: 1 } },
  //     { data: { id: "ABJ00044->jmas-1-2", source: "ABJ00044", target: "jmas-1-2", value: 1 } },
  //     { data: { id: "ABJ00044->jmas-2-2", source: "ABJ00044", target: "jmas-2-2", value: 1 } },
  //     { data: { id: "AB000059->jmas-2-2", source: "AB000059", target: "jmas-2-2", value: 1 } },
  //     {
  //       data: {
  //         id: "jmas-1-4a-e1->jmas-1-4a-e1-c1",
  //         source: "jmas-1-4a-e1",
  //         target: "jmas-1-4a-e1-c1",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-1-4a-e1->jmas-1-4a-e1-c2",
  //         source: "jmas-1-4a-e1",
  //         target: "jmas-1-4a-e1-c2",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-1-4a-e1->jmas-1-4a-e1-c3",
  //         source: "jmas-1-4a-e1",
  //         target: "jmas-1-4a-e1-c3",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-2-e1->jmas-3-2-e1-c1",
  //         source: "jmas-3-2-e1",
  //         target: "jmas-3-2-e1-c1",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-2-e1->jmas-3-2-e1-c2",
  //         source: "jmas-3-2-e1",
  //         target: "jmas-3-2-e1-c2",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-2-e1->jmas-3-2-e1-c3",
  //         source: "jmas-3-2-e1",
  //         target: "jmas-3-2-e1-c3",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-1-4a->jmas-1-4a-e1",
  //         source: "jmas-1-4a",
  //         target: "jmas-1-4a-e1",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "ABJ00190->jmas-1-4a-e1",
  //         source: "ABJ00190",
  //         target: "jmas-1-4a-e1",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "AB000542->jmas-1-4a-e1",
  //         source: "AB000542",
  //         target: "jmas-1-4a-e1",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "AB000204->jmas-1-4a-e1",
  //         source: "AB000204",
  //         target: "jmas-1-4a-e1",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: { id: "ABJ00190->jmas-3-2-e1", source: "ABJ00190", target: "jmas-3-2-e1", value: 1 },
  //     },
  //     {
  //       data: { id: "ABJ00302->jmas-3-2-e1", source: "ABJ00302", target: "jmas-3-2-e1", value: 1 },
  //     },
  //     {
  //       data: { id: "AB000204->jmas-3-2-e1", source: "AB000204", target: "jmas-3-2-e1", value: 1 },
  //     },
  //     {
  //       data: { id: "jmas-3-2->jmas-3-2-e1", source: "jmas-3-2", target: "jmas-3-2-e1", value: 1 },
  //     },
  //     {
  //       data: {
  //         id: "jmas-1-4a-e1->jmas-1-4a-e1-c4",
  //         source: "jmas-1-4a-e1",
  //         target: "jmas-1-4a-e1-c4",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-1-4a-e1->jmas-1-4a-e1-c7",
  //         source: "jmas-1-4a-e1",
  //         target: "jmas-1-4a-e1-c7",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-2-e1->jmas-3-2-e1-c4",
  //         source: "jmas-3-2-e1",
  //         target: "jmas-3-2-e1-c4",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-2-e1->jmas-3-2-e1-c5",
  //         source: "jmas-3-2-e1",
  //         target: "jmas-3-2-e1-c5",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-2-e1->jmas-3-2-e1-c6",
  //         source: "jmas-3-2-e1",
  //         target: "jmas-3-2-e1-c6",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-2-e1->jmas-3-2-e1-c7",
  //         source: "jmas-3-2-e1",
  //         target: "jmas-3-2-e1-c7",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-1-4a-e1->jmas-1-4a-e1-c5",
  //         source: "jmas-1-4a-e1",
  //         target: "jmas-1-4a-e1-c5",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-1-4a-e1->jmas-1-4a-e1-c6",
  //         source: "jmas-1-4a-e1",
  //         target: "jmas-1-4a-e1-c6",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-1-e1->jmas-3-1-e1-c1",
  //         source: "jmas-3-1-e1",
  //         target: "jmas-3-1-e1-c1",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-1-e1->jmas-3-1-e1-c2",
  //         source: "jmas-3-1-e1",
  //         target: "jmas-3-1-e1-c2",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-1-e1->jmas-3-1-e1-c3",
  //         source: "jmas-3-1-e1",
  //         target: "jmas-3-1-e1-c3",
  //         value: 1,
  //       },
  //     },
  //     {
  //       data: {
  //         id: "jmas-3-1-e1->jmas-3-1-e1-c4",
  //         source: "jmas-3-1-e1",
  //         target: "jmas-3-1-e1-c4",
  //         value: 1,
  //       },
  //     },
  //     { data: { id: "ABJ00044->jmas-3-1", source: "ABJ00044", target: "jmas-3-1", value: 1 } },
  //     { data: { id: "AB000318->jmas-3-1", source: "AB000318", target: "jmas-3-1", value: 1 } },
  //     { data: { id: "ABJ00044->jmas-1-3", source: "ABJ00044", target: "jmas-1-3", value: 1 } },
  //     { data: { id: "AB000318->jmas-3-2", source: "AB000318", target: "jmas-3-2", value: 1 } },
  //     {
  //       data: { id: "ABJ00190->jmas-3-1-e1", source: "ABJ00190", target: "jmas-3-1-e1", value: 1 },
  //     },
  //     {
  //       data: { id: "ABJ00302->jmas-3-1-e1", source: "ABJ00302", target: "jmas-3-1-e1", value: 1 },
  //     },
  //     {
  //       data: { id: "AB000204->jmas-3-1-e1", source: "AB000204", target: "jmas-3-1-e1", value: 1 },
  //     },
  //     {
  //       data: { id: "jmas-3-1->jmas-3-1-e1", source: "jmas-3-1", target: "jmas-3-1-e1", value: 1 },
  //     },
  //   ],
  // };

  /* eslint-disable-next-line no-unused-vars */
  var cy = cytoscape({
    container: document.getElementById("cy"), // container to render in

    elements: graphData,
    style: [
      {
        selector: "node",
        style: {
          "background-color": "#11479e",
          label: "data(id)",
        },
      },

      {
        selector: "edge",
        style: {
          width: 4,
          "target-arrow-shape": "triangle",
          "line-color": "#9dbaea",
          "target-arrow-color": "#9dbaea",
          "curve-style": "bezier",
        },
      },
    ],

    layout: {
      name: "cola", //"klay", //"cola",// "dagre"
      animate: true,
      infinite: true, // for cola, animate continuously
      // nodeSpacing: () =>  30,
      // flow: { axis: 'y', minSeparation: 70 },
      // edgeJaccardLength: 70,
    },
  });
}
