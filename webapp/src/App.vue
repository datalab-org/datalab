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
    // Wait for the router to resolve the initial route before loading schemas,
    // so that redirect-only routes (e.g., /files/*) can navigate away
    // without triggering unnecessary API requests.
    await this.$router.isReady();
    if (this.$route.name === "files-redirect") return;
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
  color: #2c3e50;
}

#nav {
  padding: 30px;
  text-align: center;
}

#nav a {
  color: #444;
  border-radius: 5px;
  padding: 5px;
}

#nav a.router-link-exact-active {
  color: black;
  font-weight: bold;
  text-decoration: underline;
}

/*for form errors*/
.red-border {
  border-color: red;
}

/*recover btn-default from bootstrap 3*/
.btn-default {
  color: #333;
  background-color: #fff;
  border-color: #ccc;
}
.btn-default:focus {
  color: #333;
  background-color: #e6e6e6;
  border-color: #8c8c8c;
}
.btn-default:hover {
  color: #333;
  background-color: #e6e6e6;
  border-color: #adadad;
}
.btn-default:active,
.btn-default.active {
  color: #333;
  font-weight: bold;
  background-color: #e6e6e6;
  border-color: #000000;
  border-width: 1px;
}

.callout {
  padding: 1.25rem;
  margin-top: 1.25rem;
  margin-bottom: 1.25rem;
  border: 1px solid #e9ecef;
  border-left-width: 0.25rem;
  border-radius: 0.25rem;
}
.callout-info {
  border-left-color: #5bc0de;
}

.callout-warning {
  border-left-color: #f0ad4e;
}

.callout-danger {
  border-left-color: #d9534f;
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
