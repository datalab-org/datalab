<template>
	<div class="tree-menu">
		<div @click="toggleChildren">{{ label }} ({{nodes? nodes.length : 0}} children {{showChildren? "shown" : " hidden"}})</div>
		<div v-if="showChildren">
		<ol :style="{'margin-left': depth*2 + ' rem'}">
			<li v-for="(node, index) in nodes" :key="'treeElement' + index">
				<tree-menu
					:nodes="node.nodes" 
					:label="node.label"
					:depth="depth + 1"
				/>
			</li>
		</ol>
		</div>
	</div>
</template>

<script>
	export default { 
		props: [ 'label', 'nodes', 'depth' ],
		data() {
			return { showChildren: false }
		},
		name: 'tree-menu',
		computed: {
			indent() {
				return { transform: `translate(${this.depth * 50}px)` }
			}
		},
		methods: {
			toggleChildren() {
				this.showChildren = !this.showChildren;
			}
		}
	}
</script>
