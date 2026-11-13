import { createRouter, createMemoryHistory } from "vue-router";

import ToggleableTagsFormGroup from "@/components/ToggleableTagsFormGroup.vue";

describe("ToggleableTagsFormGroup", () => {
  it("links directly to Tag management in Settings", () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/settings", name: "settings", component: { template: "<div />" } }],
    });

    cy.mount(ToggleableTagsFormGroup, {
      props: { modelValue: [] },
      global: {
        plugins: [router],
        stubs: {
          FontAwesomeIcon: true,
          TagList: true,
          TagSelect: true,
        },
      },
    });

    cy.get('a[aria-label="Manage tags"]')
      .should("have.attr", "href", "/settings?section=tags")
      .and("have.attr", "target", "_blank")
      .and("have.attr", "rel", "noopener");
  });
});
