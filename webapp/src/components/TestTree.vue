<template>
	<h3>Test of data tree</h3>
	<tree-menu 
		:nodes="treeData.nodes" 
		:depth="0"   
		:label="treeData.label"
	>
	</tree-menu>
</template>

<script>
	import TreeMenu from "@/components/TreeMenu.vue"
	export default { 
		data() {
			return {
				treeData : {
					label: 'root',
					nodes: [
						{
							label: 'item1',
							nodes: [
								{	label: 'item1.1' },
								{	
									label: 'item1.2',
									nodes: [
										{ label: 'item1.2.1' }
									]
								}
							]
						},
						{ label: 'item2' },
					]
				}
			}
		},
		components: {
			TreeMenu
		}
	}
</script>
