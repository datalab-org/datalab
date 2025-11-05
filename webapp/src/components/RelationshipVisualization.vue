<template>
  <label class="mr-2">Relationships</label>
  <ul class="nav nav-tabs">
    <li class="nav-item">
      <a
        class="nav-link"
        :class="{ active: activeTab == 'parents' }"
        href="#"
        @click.prevent="activeTab = 'parents'"
      >
        Parents
      </a>
    </li>
    <li class="nav-item">
      <a
        class="nav-link"
        :class="{ active: activeTab == 'children' }"
        href="#"
        @click.prevent="activeTab = 'children'"
      >
        Children
      </a>
    </li>
    <li class="nav-item">
      <a
        class="nav-link"
        :class="{ active: activeTab == 'graph' }"
        href="#"
        @click.prevent="activeTab = 'graph'"
      >
        Graph
      </a>
    </li>
  </ul>

  <div class="card">
    <div class="card-body">
      <ul v-show="activeTab == 'parents'" id="contents-ol">
        <li v-for="parent in parents" :key="parent" class="contents-item">
          <span class="contents-blocktitle" @click="openEditPageInNewTab(parent)">{{
            parent
          }}</span>
        </li>
      </ul>
      <ul v-show="activeTab == 'children'" id="contents-ol">
        <li v-for="child in children" :key="child" class="contents-item">
          <span class="contents-blocktitle" @click="openEditPageInNewTab(child)">{{ child }}</span>
        </li>
      </ul>
      <div v-show="activeTab == 'graph'" style="position: relative">
        <div
          v-if="isLoading"
          class="position-absolute w-100 h-100 top-0 start-0 d-flex justify-content-center align-items-center"
          style="background-color: rgba(255, 255, 255, 0.7); z-index: 100"
        >
          <div class="card p-3 shadow-sm">
            <div class="text-center">
              <font-awesome-icon
                :icon="['fa', 'sync']"
                class="fa-2x text-primary mb-2"
                :spin="true"
                aria-label="loading"
              />
              <p class="mb-0 fw-medium">Loading graph...</p>
            </div>
          </div>
        </div>
        <ItemGraph :graph-data="graphData" style="height: 400px" />
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
  components: {
    // FormattedItemName
    ItemGraph,
  },
  props: {
    item_id: { type: String, required: true },
  },
  data() {
    return {
      activeTab: "graph",
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
    isLoading() {
      return this.$store.state.itemGraphIsLoading;
    },
  },
  mounted() {
    getItemGraph({ item_id: this.item_id });
  },
  methods: {
    openEditPageInNewTab(item_id) {
      window.open(`/edit/${item_id}`, "_blank");
    },
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

.contents-blocktitle {
  color: #004175;
}

#contents-ol {
  margin-bottom: 0rem;
  padding-left: 1rem;
}
</style>
