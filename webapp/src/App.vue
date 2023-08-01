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
@import url("https://fonts.googleapis.com/css?family=Spline+Sans+Mono");
@import url("https://fonts.googleapis.com/css?family=Major+Mono+Display");

#app {
  font-family: Figtree, Avenir, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  /*text-align: center;*/
  color: #2c3e50;
  font-size: 12px;
}

input {
  font-size: 12px;
}

.form-control {
  font-size: 12px;
  border: 1px solid #ced4da;
  border-radius: 0;
}

.card {
  border-radius: 0;
  border: 0;
}

.card-component {
  padding-bottom: 10px;
}

label,
.contents-item,
.contents-blocktitle,
.nav-item,
.navbar-type,
.subheading {
  font-family: "Spline Sans Mono";
  text-transform: uppercase;
}

.select-table {
  font-size: 1em;
}

.subheading {
  font-family: "Spline Sans Mono";
  font-size: 1em;
}

.navbar-type {
  padding-right: 10px;
  vertical-align: middle;
}

.dropdown-menu {
  border-radius: 0;
}

.dropdown-item {
  font-size: 12px;
  color: black;
}

.dropdown-item:hover {
  text-decoration: underline wavy darkred;
  text-underline-offset: 0.2rem;
  background-color: white;
}

.datalab-title {
  font-size: 5em;
  text-decoration: underline wavy lightgrey;
  text-underline-offset: -0.4em;
  text-decoration-skip-ink: none;
  text-decoration-thickness: 2.5px;
  font-weight: bold;
  text-align: center;
  font-family: Major Mono Display;
}

.datalab-D {
  color: black;
}

.datalab-A {
  color: rgb(173, 20, 28);
  text-transform: lowercase;
}

.datalab-T {
  color: navy;
}

.datalab-AA {
  color: rgb(173, 20, 28);
}

.datalab-L {
  color: navy;
}

.datalab-AAA {
  color: rgb(173, 20, 28);
  text-transform: lowercase;
}

.datalab-B {
  color: gold;
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

#nav a {
  font-family: "Spline Sans Mono";
  text-transform: uppercase;
  font-weight: normal;
}

#nav a.router-link-exact-active {
  color: #42b983;
  text-decoration: underline wavy;
  text-underline-offset: 0.2rem;
}

/*for form errors*/
.red-border {
  border-color: red;
}

.item-table {
  background-color: white;
}

.item-tr {
  font-family: "Figtree";
  font-size: 1em;
  padding: 10px;
  margin: 10px;
  border: none;
}

.table-item-type {
  text-transform: uppercase;
  font-family: "Spline Sans Mono";
  font-size: 0.8em;
  vertical-align: middle;
  padding: 10px;
  margin: 10px;
}

.item-td {
  display: table-cell;
  border-left: 1px dotted #ddd;
  border-right: 1px dotted #ddd;
  border-bottom: none;
  border-top: none;
  vertical-align: middle;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.table-item-delete-button {
  border-right: none;
  border-top: none;
  border-bottom: none;
}

.item-th {
  font-family: "Spline Sans Mono";
  font-size: 1em;
  text-transform: uppercase;
  font-weight: normal;
  border-left: 1px solid #ddd;
  vertical-align: middle;
  border-right: 1px solid #ddd;
}

.table-item-name {
  font-family: "Spline Sans Mono";
  font-size: 0.8em;
  font-style: italic;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 250px;
}

.table-item-date {
  font-family: "Spline Sans Mono";
  font-size: 0.8em;
  color: grey;
}

/*recover btn-default from bootstrap 3*/
.btn-default {
  color: #333;
  font-size: 1em;
  background-color: #fff;
  border-color: #ccc;
  font-family: "Spline Sans Mono";
  text-transform: uppercase;
  padding: 5;
  border-radius: 0;
}
.btn-default:focus {
  color: #333;
  background-color: #e6e6e6;
  border-color: #8c8c8c;
}
.btn-default:hover {
  color: #333;
  /*background-color: #e6e6e6;*/
  border-color: #adadad;
  text-decoration: underline wavy darkred;
  text-underline-offset: 0.2rem;
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

.badge {
  border: 2px solid transparent;
  font-family: "Spline Sans Mono", monospace;
  font-weight: normal;
  border-radius: 0;
}

.badge.clickable:hover {
  cursor: pointer;
  box-shadow: grey 1px 1px 1px 1px;
}
</style>
