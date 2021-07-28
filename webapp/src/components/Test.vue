<template>
  <div class="file-group" v-for="filename in files" :key="filename">
    <font-awesome-icon
      icon="times"
      fixed-width
      class="delete-file-button"
      @click.prevent="deleteFile($event, filename)"
    />
    <a class="filelink" target="_blank" :href="`#`">{{ filename }}</a>
  </div>
</template>

<script>
export default {
  data() {
    return {
      files: ["file1", "file2", "file3", "file4"],
    };
  },
  methods: {
    deleteFile(event, filename) {
      console.log("delete pressed for " + filename);
      console.log(event);
      const index = this.files.indexOf(filename);
      if (index > -1) {
        this.files.splice(index, 1);
      }
    },
  },
};
</script>

<style>
.delete-file-button {
  padding-right: 0.5rem;
  color: gray;
  cursor: pointer;
}
</style>
