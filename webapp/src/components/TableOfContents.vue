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
        <div ref="sidenavScroll" class="sidenav-scroll" @scroll="checkOverflowSoon">
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
        <div v-if="sidenavHasMore" class="contents-more-indicator">⋯</div>
      </div>
    </transition>
    <label class="mr-2">Contents</label>
    <div class="card">
      <div ref="cardScroll" class="card-body overflow-auto" @scroll="checkOverflowSoon">
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
      <div v-if="cardHasMore" class="contents-more-indicator">⋯</div>
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
      sidenavHasMore: false,
      cardHasMore: false,
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
  watch: {
    sidebarShown() {
      this.checkOverflowSoon();
    },
    display_order() {
      this.checkOverflowSoon();
    },
  },
  mounted() {
    this.checkOverflow();
    window.addEventListener("resize", this.checkOverflowSoon);
  },
  beforeUnmount() {
    window.removeEventListener("resize", this.checkOverflowSoon);
  },
  methods: {
    scrollToID(event, id) {
      var element = document.getElementById(id);
      element.scrollIntoView({ behavior: "smooth" });
    },
    // Whether a scrollable element still has content hidden below its
    // visible area, i.e. it isn't scrolled all the way to the bottom.
    hasMoreBelow(el) {
      return !!el && el.scrollHeight - el.scrollTop - el.clientHeight > 1;
    },
    checkOverflow() {
      this.sidenavHasMore = this.hasMoreBelow(this.$refs.sidenavScroll);
      this.cardHasMore = this.hasMoreBelow(this.$refs.cardScroll);
    },
    checkOverflowSoon() {
      this.$nextTick(this.checkOverflow);
    },
  },
};
</script>

<style scoped>
.contents-item {
  cursor: pointer;
}

.card {
  position: relative;
}

.card-body.overflow-auto {
  max-height: 60vh;
}

.contents-more-indicator {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0.25rem 0 0.1rem;
  text-align: center;
  font-size: 1.2rem;
  line-height: 1;
  letter-spacing: 0.15em;
  color: #6c757d;
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0), rgba(255, 255, 255, 0.9) 55%);
  pointer-events: none;
}

.contents-blocktitle {
  color: #004175;
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
  background: #fff;
  border-width: 1px;
  border-color: lightgrey;
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
  background: #fff;
  padding: 1rem 1rem;
  margin-top: 3rem;
  border-radius: 0px 5px 5px 0px;
  border-width: 1px;
  border-color: lightgrey;
  border-style: solid;
}

.sidenav-scroll {
  overflow-x: hidden;
  overflow-y: auto;
  max-height: calc(100vh - 8rem);
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
  color: #2196f3;
  display: block;
}

.sidenav a:hover {
  color: #064579;
}
</style>

<style>
.editor-body {
  margin-left: v-bind("sidebarWidth+'px'");
}
</style>
