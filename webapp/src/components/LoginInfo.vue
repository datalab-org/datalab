<template>
  <h1 style="font-size: 4rem">Welcome to Datalab</h1>
  <p>datalab is a place to store experimental data and the connections between them.</p>
  <p>
    datalab is open source (MIT license) and development occurs on GitHub at
    <a href="https://github.com/datalab-org/datalab"
      ><font-awesome-icon :icon="['fab', 'github']" />&nbsp;datalab-org/datalab</a
    >
    with documentation available on
    <a href="https://the-datalab.readthedocs.io"
      ><font-awesome-icon icon="book" />&nbsp;ReadTheDocs</a
    >.
  </p>
  <router-link to="/about" class="btn btn-default">Learn More</router-link>
</template>

<script>
export default {
  name: "LoginInfo",
};
</script>
