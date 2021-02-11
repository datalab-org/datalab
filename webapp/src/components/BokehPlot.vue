<template>
	<div v-if="!loaded" class="alert alert-info"> Hello, a bokeh plot will be placed here </div>
	<div v-if="loading" class="alert alert-warning"> Setting up bokeh plot... </div>
	<!-- <button class="btn btn-dark" @click="startBokehPlot"> Setup plot </button> -->
	<!-- <button class="btn btn-dark" @click="cleanupBokehPlot"> Remove plot </button> -->
	<div ref="bokehPlotContainer" :id="unique_id" :style="{height: bokehPlotContainerHeight}"/> 
</template>

<script>

import * as Bokeh from "bokeh"
// var BokehDoc = null

export default {
	props: ['bokehPlotData'],
	data: function () {
		return {
			unique_id: "dummy-bokeh-id",
			loading: false,
			loaded: false,
			bokeh_views: null,
			bokehPlotContainerHeight: 'auto'
		}
	},
	// BokehDoc: null, // this is a non-reactive property. We don't put this is in Data so Vue doesn't wrap it in a Proxy, which breaks its document.clear() functionality (for some reason)
	methods: {
		async startBokehPlot() {
			if (this.bokehPlotData) {
				this.loading = true
				console.log("running startBokehPlot with:");
				console.log(this.bokehPlotData);
				var views = await Bokeh.embed.embed_item(this.bokehPlotData, this.unique_id);
				this.BokehDoc = views[0].model.document // NOTE: BokehDoc is not in data, so this is NONREACTIVE. (we need to be the case or BokehDoc.clear() doesn't work for some reason)
				this.bokeh_views = views
				console.log("Bokeh Doc:")
				console.log(this.BokehDoc)
				this.loading = false
				this.loaded = true
			}
		},
		cleanupBokehPlot() {
			if (this.BokehDoc) {
				console.log("cleaning up bokeh plot")
				this.BokehDoc.clear();
				const i = Bokeh.documents.indexOf(this.BokehDoc);
				if (i > -1) {
					Bokeh.documents.splice(i, 1);
				}
			}
		},
		guidGenerator() {
			var S4 = function() {
				return (((1+Math.random())*0x10000)|0).toString(16).substring(1);
			};
			return (S4()+S4()+"-"+S4());
		}
	},
	watch: {
		bokehPlotData() {
			var scrollHeight = this.$refs.bokehPlotContainer.scrollHeight
			this.bokehPlotContainerHeight = `${scrollHeight}px`
			this.cleanupBokehPlot()
			this.startBokehPlot()
			window.requestAnimationFrame( () => {this.bokehPlotContainerHeight = 'auto'});
			// this.bokehPlotContainerHeight = 'auto'
		}
	},
	mounted() {
		this.unique_id = this.guidGenerator()
		this.startBokehPlot()
	},
	unmounted() {
		this.cleanupBokehPlot()
	}
}
</script>