<template>
  <!-- <div id="nav"> -->
  <!-- <router-link to="/">Home</router-link> | -->
  <!-- <router-link to="/about">About</router-link> | -->
  <!-- <router-link to="/test">Test Page</router-link> |  -->
  <!-- <router-link to="/samples">Samples</router-link> -->
  <!-- </div> -->
  <router-view />
</template>

<style>
body {
  margin: 0rem !important; /* for some reason, tinymce sets margin 1rem globally :o */
}

* {
  scroll-margin-top: 3.5rem;
}

@import url("https://fonts.googleapis.com/css?family=Figtree");
@import url("https://fonts.googleapis.com/css?family=Roboto+Mono");
#app {
  font-family: Figtree, Avenir, Arial, sans-serif;
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
  font-weight: bold;
  color: #2c3e50;
  border-radius: 5px;
  padding: 5px;
}

#nav a.router-link-exact-active {
  color: #42b983;
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

.table-item-id {
  font-size: 1.2em;
  font-weight: normal;
}

.formatted-refcode {
  font-size: 1.2em;
  font-weight: normal;
  font-family: "Roboto Mono", monospace;
}
</style>
