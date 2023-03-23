<template>
  <label class="mr-2">Relationships</label>
  <ul class="nav nav-tabs">
    <li class="nav-item">
      <a
        class="nav-link"
        :class="{ active: activeTab == 'parents' }"
        @click.prevent="activeTab = 'parents'"
        href="#"
      >
        Parents
      </a>
    </li>
    <li class="nav-item">
      <a
        class="nav-link"
        :class="{ active: activeTab == 'children' }"
        @click.prevent="activeTab = 'children'"
        href="#"
      >
        Children
      </a>
    </li>
    <li class="nav-item">
      <a
        class="nav-link"
        :class="{ active: activeTab == 'graph' }"
        @click.prevent="activeTab = 'graph'"
        href="#"
      >
        Graph
      </a>
    </li>
  </ul>

  <div class="card">
    <div class="card-body">
      <ul id="contents-ol" v-show="activeTab == 'parents'">
        <li class="contents-item" v-for="parent in parents" :key="parent">
          <span class="contents-blocktitle" @click="openEditPageInNewTab(parent)">{{
            parent
          }}</span>
        </li>
      </ul>
      <ul id="contents-ol" v-show="activeTab == 'children'">
        <li class="contents-item" v-for="child in children" :key="child">
          <span class="contents-blocktitle" @click="openEditPageInNewTab(child)">{{ child }}</span>
        </li>
      </ul>
      <div v-show="activeTab == 'graph'">
        <ItemGraph :graphData="graphData" style="height: 400px" />
      </div>
      <!--       <div class="alert alert-info" role="alert" v-show="activeTab == 'graph'">
        Graph view not yet implemented
      </div> -->
    </div>
  </div>
</template>

<script>
// import FormattedItemName from "@/components/FormattedItemName"
import ItemGraph from "@/components/ItemGraph";
import { getItemGraph } from "@/server_fetch_utils.js";

export default {
  data() {
    return {
      activeTab: "parents",
    };
  },
  computed: {
    parents() {
      return this.$store.state.all_item_parents[this.item_id];
    },
    children() {
      return this.$store.state.all_item_children[this.item_id];
    },
    graphData() {
      return this.$store.state.itemGraphData;
    },
  },
  methods: {
    openEditPageInNewTab(item_id) {
      window.open(`/edit/${item_id}`, "_blank");
    },
  },
  props: {
    item_id: String,
  },
  async mounted() {
    await getItemGraph(this.item_id);
  },
  components: {
    // FormattedItemName
    ItemGraph,
  },
};
</script>

<style scoped>
.nav-link {
  cursor: pointer;
}

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
