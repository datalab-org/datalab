module.exports = {
  root: true,
  env: {
    node: true,
    "cypress/globals": true,
  },
  extends: [
    "plugin:vue/vue3-recommended",
    "eslint:recommended",
    "plugin:prettier/recommended",
    "@vue/prettier",
    "plugin:cypress/recommended",
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true  // This is all we need for parsing JSX
    }
  },
  rules: {
    //"no-console": process.env.NODE_ENV === "production" ? "warn" : "off",
    "no-debugger": process.env.NODE_ENV === "production" ? "warn" : "off",
    "vue/multi-word-component-names": "off",
    // Rule disable for item_id, block_id and collection_id
    "vue/prop-name-casing": "off",
    "vue/no-unused-components": process.env.NODE_ENV === "production" ? "error" : "warn",
    "vue/no-unused-vars": process.env.NODE_ENV === "production" ? "error" : "warn",
    "cypress/no-assigning-return-values": "warn",
    "cypress/no-unnecessary-waiting": "warn",
    "cypress/unsafe-to-chain-command": "warn",
    "prettier/prettier": process.env.NODE_ENV === "production" ? "error" : "warn",
  },
};
