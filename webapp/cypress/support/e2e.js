// ***********************************************************
// This example support/index.js is processed and
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

// Type instantly rather than at the default 10 ms per keystroke; the tests type ~2000
// characters in total, so the delay adds up without exercising anything extra
Cypress.Keyboard.defaults({ keystrokeDelay: 0 });

// eslint-disable-next-line no-unused-vars
Cypress.on("uncaught:exception", (err, runnable) => {
  // returning false here prevents Cypress from
  // failing the test
  return false;
});
