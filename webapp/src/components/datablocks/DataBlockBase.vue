<template>
  <div :id="block_id" class="data-block">
    <div class="datablock-header collapsible" :class="{ expanded: isExpanded }">
      <font-awesome-icon
        :icon="['fas', 'chevron-right']"
        fixed-width
        class="collapse-arrow"
        @click="toggleExpandBlock"
      />
      <font-awesome-icon :icon="['fas', 'cubes']" fixed-width />
      <input v-model="BlockTitle" class="form-control-plaintext block-title" type="text" />
      <span class="blocktype-label ml-auto mr-3 d-inline" style="white-space: nowrap">
        {{ blockType }}
      </span>
      <span v-if="blockInfo" class="block-header-icon"
        ><StyledBlockInfo :block-info="blockInfo"
      /></span>
      <font-awesome-icon
        :icon="['fa', 'sync']"
        class="block-header-icon"
        :class="{ spin: isUpdating }"
        aria-label="updateBlock"
        @click="updateBlock"
      />
      <font-awesome-icon
        v-if="displayIndex != 0"
        :icon="['fas', 'arrow-up']"
        class="block-header-icon"
        @click="swapUp"
      />
      <font-awesome-icon
        v-if="displayIndex != displayOrder.length - 1"
        :icon="['fas', 'arrow-down']"
        class="block-header-icon"
        @click="swapDown"
      />
      <font-awesome-icon
        :icon="['fas', 'times']"
        class="block-header-icon delete-block-button"
        @click="deleteThisBlock"
      />
    </div>

    <div
      ref="datablockContent"
      :style="{ 'max-height': contentMaxHeight }"
      class="datablock-content position-relative"
    >
      <!-- Show any warnings or errors reported by the block -->
      <div
        v-if="block.errors"
        ref="errorsContent"
        class="alert alert-danger d-flex align-items-center ml-3"
        :class="{ expanded: isErrorsExpanded }"
        role="alert"
      >
        <font-awesome-icon
          :icon="['fas', 'chevron-right']"
          fixed-width
          class="collapse-arrow"
          @click="toggleExpandErrors"
        />
        <ul v-if="isErrorsExpanded" class="fa-ul">
          <li v-for="(error, index) in block.errors.slice(0, 5)" :key="index">
            <font-awesome-icon class="fa-li" icon="exclamation-circle" />
            {{ error }}
          </li>
          <p v-if="block.errors.length > 5">
            And {{ block.errors - 5 }} more error{{ block.errors.length - 5 > 1 ? "s" : "" }} ...
          </p>
        </ul>
        <ul v-if="!isErrorsExpanded" class="fa-ul">
          <li>
            <font-awesome-icon class="fa-li" icon="exclamation-circle" />
            {{ block.errors.length }} error(s) (click to expand)
          </li>
        </ul>
      </div>
      <div
        v-if="block.warnings"
        ref="warningsContent"
        class="alert alert-warning d-flex align-items-center ml-3"
        :class="{ expanded: isWarningsExpanded }"
        role="alert"
      >
        <font-awesome-icon
          :icon="['fas', 'chevron-right']"
          fixed-width
          class="collapse-arrow"
          @click="toggleExpandWarnings"
        />
        <ul v-if="isWarningsExpanded" class="fa-ul">
          <li v-for="(warning, index) in block.warnings.slice(0, 5)" :key="index">
            <font-awesome-icon class="fa-li" icon="exclamation-triangle" />
            {{ warning }}
          </li>
          <p v-if="block.warnings.length > 5">
            And {{ block.warnings.length - 5 }} more warning{{
              block.warnings.length - 5 > 1 ? "s" : ""
            }}
            ...
          </p>
        </ul>
        <ul v-if="!isWarningsExpanded" class="fa-ul">
          <li>
            <font-awesome-icon class="fa-li" icon="exclamation-triangle" />
            {{ block.warnings.length }} warning(s) (click to expand)
          </li>
        </ul>
      </div>
      <div
        v-if="showOverlay"
        class="position-absolute w-100 h-100 top-0 start-0 d-flex justify-content-center align-items-center"
        style="background-color: rgba(255, 255, 255, 0.7); z-index: 100"
        data-testid="loading-overlay"
      >
        <div class="card p-3 shadow-sm">
          <div class="text-center">
            <font-awesome-icon
              :icon="['fa', 'sync']"
              class="fa-2x text-primary mb-2"
              :spin="true"
              aria-label="loading"
            />
            <p class="mb-0 fw-medium">Loading data...</p>
          </div>
        </div>
      </div>
      <slot></slot>
      <TinyMceInline v-model="BlockDescription" data-testid="block-description"></TinyMceInline>
    </div>
  </div>
</template>

<script>
/**
 * DataBlockBase - A base component for all data blocks.
 *
 * This component is used to create a data block that can be expanded, collapsed,
 * moved, deleted and annotated with a title and description.
 *
 */
import { createComputedSetterForBlockField } from "@/field_utils.js";
import TinyMceInline from "@/components/TinyMceInline";
import StyledBlockInfo from "@/components/StyledBlockInfo";
import tinymce from "tinymce/tinymce";

import { deleteBlock, updateBlockFromServer } from "@/server_fetch_utils";

export default {
  components: {
    TinyMceInline,
    StyledBlockInfo,
  },
  props: {
    item_id: {
      type: String,
      required: true,
    },
    block_id: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      isExpanded: true,
      contentMaxHeight: "none",
      padding_height: 18,
      isErrorsExpanded: true,
      isWarningsExpanded: true,
    };
  },
  computed: {
    block() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id];
    },
    blockType() {
      try {
        return this.block["blocktype"];
      } catch {
        return "Block type not found";
      }
    },
    displayOrder() {
      return this.$store.state.all_item_data[this.item_id].display_order;
    },
    displayIndex() {
      // var display_order = this.$store.state.all_item_data[this.item_id].display_order
      return this.displayOrder.indexOf(this.block_id);
    },
    isUpdating() {
      return this.$store.state.updatingDelayed[this.block_id];
    },
    blockInfo() {
      return this.$store.state.blocksInfos?.[this.blockType];
    },
    showOverlay() {
      return this.isUpdating && this.isExpanded;
    },
    BlockTitle: createComputedSetterForBlockField("title"),
    BlockDescription: createComputedSetterForBlockField("freeform_comment"),
  },
  mounted() {
    // this is to help toggleExpandBlock() work properly. Resets contentMaxHeight to "none"
    // after expand transition finishes so that height can be set automatically if content changes
    var content = this.$refs.datablockContent;
    content.addEventListener("transitionend", () => {
      if (this.isExpanded) {
        this.contentMaxHeight = "none";
      }
    });
  },
  methods: {
    async updateBlock() {
      // check for any tinymce editors within the block. If so, trigger them
      // to save so that the store is updated before sending data to the server
      tinymce.editors.forEach((editor) => {
        // check if editor is a child of this datablock
        if (editor.bodyElement.closest(`#${this.block_id}`) && editor.isDirty()) {
          editor.save();
        }
      });
      await updateBlockFromServer(this.item_id, this.block_id, this.block);
    },
    deleteThisBlock() {
      deleteBlock(this.item_id, this.block_id);
    },
    swapUp() {
      this.$store.commit("swapBlockDisplayOrder", {
        item_id: this.item_id,
        index1: this.displayIndex,
        index2: this.displayIndex - 1,
      });
    },
    swapDown() {
      console.log("swapDown clicked!");
      this.$store.commit("swapBlockDisplayOrder", {
        item_id: this.item_id,
        index1: this.displayIndex,
        index2: this.displayIndex + 1,
      });
      // document.getElementById(this.block_id).scrollIntoView({behavior:'smooth'}) // doesn't work
    },
    toggleExpandBlock() {
      var content = this.$refs.datablockContent;
      console.log(this.contentMaxHeight);
      if (!this.isExpanded) {
        this.contentMaxHeight = content.scrollHeight + 2 * this.padding_height + "px";
        this.isExpanded = true;
      } else {
        requestAnimationFrame(() => {
          //must be an arrow function so that 'this' is still accessible!
          this.contentMaxHeight = content.scrollHeight + "px";
          requestAnimationFrame(() => {
            this.contentMaxHeight = "0px";
            this.isExpanded = false;
          });
        });
      }
    },
    toggleExpandErrors() {
      var content = this.$refs.errorsContent;
      if (!this.isErrorsExpanded) {
        this.errorsMaxHeight = content.scrollHeight + 2 * this.padding_height + "px";
        this.isErrorsExpanded = true;
      } else {
        requestAnimationFrame(() => {
          this.errorsMaxHeight = content.scrollHeight + "px";
          requestAnimationFrame(() => {
            this.errorsMaxHeight = "0px";
            this.isErrorsExpanded = false;
          });
        });
      }
    },
    toggleExpandWarnings() {
      var content = this.$refs.warningsContent;
      if (!this.isWarningsExpanded) {
        this.warningsMaxHeight = content.scrollHeight + 2 * this.padding_height + "px";
        this.isWarningsExpanded = true;
      } else {
        requestAnimationFrame(() => {
          this.warningsMaxHeight = content.scrollHeight + "px";
          requestAnimationFrame(() => {
            this.warningsMaxHeight = "0px";
            this.isWarningsExpanded = false;
          });
        });
      }
    },
  },
};
</script>

<style scoped>
.data-block {
  padding-bottom: 18px;
}

ul {
  margin-bottom: 0;
}

/* Style the button that is used to open and close the collapsible content */
.datablock-header {
  display: flex;
  align-items: center;
  font-size: large;
  height: 35px;
}

.blocktype-label {
  font-style: italic;
  color: grey;
}

.collapsible {
  background-color: #eee;
  color: #444;
  /*cursor: pointer;*/
  /*padding: 6px;*/
  width: 100%;
  border: 1px solid #ccc;
  text-align: left;
  outline: none;
  border-radius: 3px;
}

.block-title {
  margin-left: 1em;
  font-size: large;
  font-weight: 500;
}

/* Add a background color to the button if it is clicked on (add the .active class with JS), and when you move the mouse over it (hover) */
/*.active, .collapsible:hover {
  background-color: #ccc;
}*/

/* Style the collapsible content. */
.datablock-content {
  background-color: white;
  /*border: 1px solid #ccc;*/
  border-radius: 3px;
  max-height: 0px;
  padding: 0px 18px;
  overflow: hidden;
  transition:
    max-height 0.4s ease,
    padding 0.4s ease;
}

/*this is a sibling selector, selects the div directly after expanded*/
.expanded + div {
  padding: 18px 18px;
  max-height: none;
}

.collapse-arrow {
  font-size: large;
  margin-left: 10px;
  margin-right: 10px;
  color: #004175;
  transition: all 0.4s;
}

.collapse-arrow:hover {
  color: #7ca7ca;
}

/* expanded is on the parent (the header) */
.expanded .collapse-arrow {
  -webkit-transform: rotate(90deg);
  -moz-transform: rotate(90deg);
  transform: rotate(90deg);
}

.block-header-icon {
  font-size: large;
  color: #004175;
  /*margin-left: auto;*/
  margin-right: 10px;
  cursor: pointer;
}

.block-header-icon:hover {
  color: #7ca7ca;
}

.spin {
  animation: spin 2s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/*#collapse_icon {
  margin: -50px 0px;
}
*/
</style>
