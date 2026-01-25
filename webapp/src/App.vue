<template>
  <router-view />
  <DialogContainer />
</template>

<script>
import DialogContainer from "@/components/DialogContainer.vue";
import { getApiConfig, loadItemSchemas } from "@/server_fetch_utils.js";

export default {
  components: {
    DialogContainer,
  },
  async created() {
    // Apply saved theme on load
    const savedTheme = this.$store.state.theme;
    if (savedTheme && savedTheme !== "default") {
      document.body.classList.add(`theme-${savedTheme}`);
    }
    await loadItemSchemas();
    await getApiConfig();
  },
};
</script>

<style>
body {
  margin: 0rem !important; /* for some reason, tinymce sets margin 1rem globally :o */
  font-family: var(--font-primary) !important;
}

* {
  scroll-margin-top: 3.5rem;
}

@import url("https://fonts.googleapis.com/css?family=Figtree");
@import url("https://fonts.googleapis.com/css?family=Libre+Barcode+39+Text");
@import url("https://fonts.googleapis.com/css?family=Roboto+Mono");

:root {
  --font-primary: Figtree, Avenir, Arial, sans-serif;
  --font-monospace: "Roboto Mono", monospace;
}

#app {
  font-family: var(--font-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  /*text-align: center;*/
  color: var(--theme-body-color, #2c3e50);
}

#nav {
  padding: 30px;
  text-align: center;
}

#nav a {
  color: var(--theme-body-color, #444);
  border-radius: 5px;
  padding: 5px;
}

#nav a.router-link-exact-active {
  color: var(--theme-primary, black);
  font-weight: bold;
  text-decoration: underline;
}

/*for form errors*/
.red-border {
  border-color: red;
}

/*recover btn-default from bootstrap 3*/
.btn-default {
  color: var(--theme-body-color, #333);
  background-color: var(--theme-card-bg, #fff);
  border-color: var(--theme-border-color, #ccc);
}
.btn-default:focus {
  color: var(--theme-body-color, #333);
  background-color: var(--theme-border-color, #e6e6e6);
  border-color: var(--theme-border-color, #8c8c8c);
}
.btn-default:hover {
  color: var(--theme-body-color, #333);
  background-color: var(--theme-border-color, #e6e6e6);
  border-color: var(--theme-border-color, #adadad);
}
.btn-default:active,
.btn-default.active {
  color: var(--theme-body-color, #333);
  font-weight: bold;
  background-color: var(--theme-border-color, #e6e6e6);
  border-color: var(--theme-primary, #000000);
  border-width: 1px;
}

.callout {
  padding: 1.25rem;
  margin-top: 1.25rem;
  margin-bottom: 1.25rem;
  border: 1px solid var(--theme-border-color, #e9ecef);
  border-left-width: 0.25rem;
  border-radius: 0.25rem;
}
.callout-info {
  border-left-color: var(--theme-info, #5bc0de);
}

.callout-warning {
  border-left-color: var(--theme-warning, #f0ad4e);
}

.callout-danger {
  border-left-color: var(--theme-danger, #d9534f);
}

.fa-orcid {
  color: #a6ce39;
}

.clickable {
  cursor: pointer;
}

.modal {
  font-family: var(--font-primary);
}
</style>
