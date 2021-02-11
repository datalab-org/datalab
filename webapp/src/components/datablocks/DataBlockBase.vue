<template>
	<div :id="block_id" class="data-block">
		<div class="datablock-header collapsible" :class="{ expanded: isExpanded }">
			<font-awesome-icon :icon='["fas","chevron-right"]' fixed-width class="collapse-arrow" 
					@click="toggleExpandBlock" />
			<input class="form-control-plaintext block-title" type="text" v-model="BlockTitle">
			<span class="blocktype-label ml-auto mr-3">{{ blockType }}</span>
			<font-awesome-icon :icon='["fa","sync"]' class="block-header-icon"
				@click="updateBlock" :class="{spin: isUpdating}" />
			<font-awesome-icon :icon='["fas","arrow-up"]' class="block-header-icon"
				@click='swapUp' v-if='displayIndex != 0' />
			<font-awesome-icon :icon='["fas","arrow-down"]' class="block-header-icon"
				@click='swapDown' v-if='displayIndex != displayOrder.length-1'/>
			<font-awesome-icon :icon='["fas","times"]' class="block-header-icon delete-block-button" @click='deleteThisBlock' />
		</div>
	
		<div ref="datablockContent" :style="{'max-height': contentMaxHeight}" class="datablock-content">
			<slot></slot>
			<TinyMceInline v-model="BlockDescription"></TinyMceInline>
		</div>
	</div>
</template>

<script>

import {createComputedSetterForBlockField} from "@/field_utils.js"
import TinyMceInline from "@/components/TinyMceInline"

import { deleteBlock, updateBlockFromServer } from '@/server_fetch_utils'

export default {
	data() {
		return {
			isExpanded: true,
			contentMaxHeight: "none",
			padding_height: 18,
		}
	},
	computed: {
		block() {
			return this.$store.getters.getBlockBySampleIDandBlockID(this.sample_id, this.block_id)
		},
		blockType() { 
			try {
				return this.block["blocktype"]
			} catch {
				return "Block type not found"
			}
		},
		displayOrder() {
			return this.$store.state.all_sample_data[this.sample_id].display_order
		},
		displayIndex() {
			// var display_order = this.$store.state.all_sample_data[this.sample_id].display_order
			return this.displayOrder.indexOf(this.block_id)
		},
		isUpdating() {
			return this.$store.state.updating[this.block_id]
		},
		BlockTitle: createComputedSetterForBlockField('title'),
		BlockDescription: createComputedSetterForBlockField('freeform_comment'),
	},
	props: ["sample_id","block_id"],
	methods : {
		async updateBlock() {
			await updateBlockFromServer(this.sample_id, this.block_id, this.block)
		},
		deleteThisBlock() {
			deleteBlock(this.sample_id, this.block_id);
		},
		swapUp() {
			this.$store.commit('swapBlockDisplayOrder', {
				sample_id: this.sample_id,
				index1: this.displayIndex,
				index2: this.displayIndex-1
			})
		},
		swapDown() {
			this.$store.commit('swapBlockDisplayOrder', {
				sample_id: this.sample_id,
				index1: this.displayIndex,
				index2: this.displayIndex+1
			})
			// document.getElementById(this.block_id).scrollIntoView({behavior:'smooth'}) // doesn't work
		},
		toggleExpandBlock() {
			var content = this.$refs.datablockContent
			console.log(this.contentMaxHeight)
			if (!this.isExpanded) {
				this.contentMaxHeight = (content.scrollHeight + 2*this.padding_height) + "px";
				this.isExpanded = true;

			}
			else {
				requestAnimationFrame( () => { //must be an arrow function so that 'this' is still accessible! 
					this.contentMaxHeight = content.scrollHeight + "px";
					requestAnimationFrame( () => {
						this.contentMaxHeight = "0px";  
						this.isExpanded = false;
				})
			})
			}
		}
	},
	mounted() {
		// this is to help toggleExpandBlock() work properly. Resets contentMaxHeight to "none"
		// after expand transition finishes so that height can be set automatically if content changes
		var content =this.$refs.datablockContent
		content.addEventListener('transitionend', () => {
			if (this.isExpanded) {
				this.contentMaxHeight = "none"				
			}
		});

		this.$store.commit('setBlockNotUpdating', this.block_id)
	},
	components: {
		TinyMceInline
	}
}
</script>


<style scoped>
.data-block {
	/*outline: 1px dashed blue;*/
	padding-bottom: 18px;
	scroll-margin-top: 3.5rem;
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
  transition: max-height 0.4s ease, padding 0.4s ease;
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
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/*#collapse_icon {
  margin: -50px 0px;
}
*/

</style>




