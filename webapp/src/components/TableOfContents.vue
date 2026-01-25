<template>
  <div id="table-of-contents">
    <div class="pullout" :class="{ 'pullout-expanded': sidebarShown, 'shadow-sm': !sidebarShown }">
      <font-awesome-icon
        :icon="['fas', 'list-ol']"
        fixed-width
        class="pullout-icon"
        @click="sidebarShown = !sidebarShown"
      />
      <!-- <br> -->
      <!--       <font-awesome-icon
        :icon="['fas', 'chevron-right']"
        fixed-width
        class="collapse-icon float-right"
        :class="{'collapse-icon-rotated': sidebarShown}"
        @click="sidebarShown = !sidebarShown"
        /> -->
    </div>
    <transition name="sidebar-open">
      <div v-show="sidebarShown" class="sidenav shadow-sm">
        <!--         <font-awesome-icon
          :icon="['fas', 'chevron-right']"
          fixed-width
          class="collapse-icon float-right"
          :class="{'collapse-icon-rotated': sidebarShown}"
          @click="sidebarShown = !sidebarShown"
        /> -->
        <ol id="contents-ol">
          <li
            v-for="section in informationSections"
            :key="section.targetID"
            class="contents-item"
            @click="scrollToID($event, section.targetID)"
          >
            <span class="contents-blocktitle"> {{ section.title }} </span>
          </li>
          <li
            v-for="block_id in display_order"
            :key="block_id"
            class="contents-item"
            @click="scrollToID($event, block_id)"
          >
            <span class="contents-blocktitle">{{ blocks[block_id].title }}</span>
          </li>
        </ol>
      </div>
    </transition>
    <label class="mr-2">Contents</label>
    <div class="card">
      <div class="card-body overflow-auto">
        <ol id="contents-ol">
          <li
            v-for="section in informationSections"
            :key="section.targetID"
            class="contents-item"
            @click="scrollToID($event, section.targetID)"
          >
            <span class="contents-blocktitle"> {{ section.title }} </span>
          </li>
          <li
            v-for="block_id in display_order"
            :key="block_id"
            class="contents-item"
            @click="scrollToID($event, block_id)"
          >
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
    informationSections: { type: Array, required: true },
    item_id: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      sidebarShown: false,
      sidebarWidth: 250,
    };
  },
  computed: {
    display_order() {
      return this.$store.state.all_item_data[this.item_id]?.display_order || {};
    },
    blocks() {
      return this.$store.state.all_item_data[this.item_id]?.blocks_obj || {};
    },
    currentSidebarWidth() {
      return this.sidebarShown ? this.sidebarWidth : 0;
    },
    pulloutTransform() {
      return this.sidebarShown ? `calc(${this.sidebarWidth}px - 2.4rem)` : 0;
    },
  },
  methods: {
    scrollToID(event, id) {
      var element = document.getElementById(id);
      console.log(element);
      element.scrollIntoView({ behavior: "smooth" });
    },
  },
};
</script>

<style scoped>
.contents-item {
  cursor: pointer;
}

.contents-blocktitle {
  color: var(--theme-primary, #004175);
}

#contents-ol {
  margin-bottom: 0rem;
  padding-left: 1rem;
}

.pullout {
  position: fixed;
  z-index: 2;
  top: 2rem;
  left: 0px;
  background: var(--theme-card-bg, #fff);
  border-width: 1px;
  border-color: var(--theme-border-color, lightgrey);
  border-style: solid;
  padding: 0.5rem;
  margin-top: 3rem;
  border-radius: 0px 5px 5px 0px;
  transition: transform 0.35s ease;
}

.pullout-icon {
  font-size: large;
}

.pullout-expanded {
  transform: translateX(calc(v-bind("currentSidebarWidth+'px - 2.4rem'")));
  background: none;
  border-style: none;
  transition: transform 0.35s ease 0.05s;
  /*transition: transform 0.35s ease;*/
}

.collapse-icon {
  margin-top: 1rem;
  margin-right: -0.5rem;
  font-size: large;
  transition: transform 0.2s;
}

.collapse-icon-rotated {
  transform: rotate(180deg);
}

.sidenav {
  width: v-bind(sidebarWidth + "px");
  position: fixed;
  z-index: 1;
  top: 2rem;
  left: 0px;
  background: var(--theme-card-bg, #fff);
  overflow-x: hidden;
  padding: 1rem 1rem;
  margin-top: 3rem;
  border-radius: 0px 5px 5px 0px;
  border-width: 1px;
  border-color: var(--theme-border-color, lightgrey);
  border-style: solid;
}

.sidebar-open-enter-active,
.sidebar-open-leave-active {
  transition: transform 0.4s ease;
}

.sidebar-open-leave-to,
.sidebar-open-enter-from {
  transform: translateX(v-bind("'-' + sidebarWidth + 'px'"));
}

.sidenav a {
  padding: 6px 8px 6px 16px;
  text-decoration: none;
  font-size: 25px;
  color: var(--theme-primary, #2196f3);
  display: block;
}

.sidenav a:hover {
  color: var(--theme-muted-color, #064579);
}
</style>

<style>
.editor-body {
  margin-left: v-bind("sidebarWidth+'px'");
}
</style>
