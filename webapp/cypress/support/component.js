// ***********************************************************
// This example support/component.ts is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import "./commands";

// Alternatively you can use CommonJS syntax:
// require('./commands')

import { mount } from "cypress/vue";

Cypress.Commands.add("mount", mount);

// Component tests run in isolation without the datalab API stack, so any
// `fetch` a component fires on mount (e.g. LoginDetails -> /get-current-user,
// SampleTable -> /samples/) rejects as a network error. Tests seed the Vuex
// store directly and don't depend on the fetched data, so swallow these
// rejections instead of letting them fail unrelated assertions. Each browser
// words the rejection differently, so match all of them:
//   Chrome / Electron: "Failed to fetch"
//   Firefox:           "NetworkError when attempting to fetch resource."
//   WebKit:            "Load failed"
const FETCH_FAILURE_MESSAGES = [
  "Failed to fetch",
  "NetworkError when attempting to fetch",
  "Load failed",
];
Cypress.on("uncaught:exception", (err) => {
  if (FETCH_FAILURE_MESSAGES.some((message) => err?.message?.includes(message))) {
    return false;
  }
});

// Example use:
// cy.mount(MyComponent)
