<template>
  <div class="container">
    <label class="mr-2">Contents</label>
    <div class="card">
      <div class="card-body overflow-auto">
        <ol id="contents-ol">
          <li
            class="contents-item"
            v-for="block_id in display_order"
            :key="block_id"
            @click="scrollToID($event, block_id)"
          >
            <!-- <span class="contents-blocktype">{{ blocks[block_id].blocktype }} block</span> -->
            <!-- {{ block_id }} -->
            <span class="contents-blocktitle">{{ blocks[block_id].title }}</span>
          </li>
        </ol>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    display_order: Array,
    blocks: Object,
  },
  methods: {
    scrollToID(event, id) {
      var element = document.getElementById(id);
      element.scrollIntoView({ behavior: "smooth" });
    },
  },
};
</script>

<style scoped>
.contents-item {
  cursor: pointer;
}

.contents-blocktype {
  font-style: italic;
  color: gray;
  margin-right: 1rem;
}

.contents-blocktitle {
  color: #004175;
}

#contents-ol {
  margin-bottom: 0rem;
  padding-left: 1rem;
}
</style>
