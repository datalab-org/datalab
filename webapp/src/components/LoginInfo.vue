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
  <a
    href="https://docs.datalab-org.io/en/stable/"
    class="btn btn-default"
    target="_blank"
    rel="noopener noreferrer"
  >
    Learn More
  </a>
</template>

<script>
export default {
  name: "LoginInfo",
};
</script>
