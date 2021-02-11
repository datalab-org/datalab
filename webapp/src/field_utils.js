import store from '@/store/index.js'

// Amazingly (and perhaps dangerously) the this context used here is the this from
// the component which this function is called for. 
// For this function to work, the this context needs to have sample_id and block_id
export function createComputedSetterForBlockField(block_field) {
	return {
		get() {
			if (this.sample_id in store.state.all_sample_data) {
				return store.state.all_sample_data[this.sample_id]["blocks_obj"][this.block_id][block_field]				
			}
			else { return "" }
		},
		set(value) {
			store.commit('updateBlockData', {
				sample_id: this.sample_id,
				block_id: this.block_id, 
				block_data: {[block_field]: value}
			})
		}
	}
}

export function createComputedSetterForSampleField(sample_field) {
	return {
		get() {
			if (this.sample_id in store.state.all_sample_data) {
				return store.state.all_sample_data[this.sample_id][sample_field]
			}
		},
		set(value) {
			console.log('comp setter called with value:')
			console.log(value)
			store.commit('updateSampleData', {
				sample_id: this.sample_id,
				block_data: {[sample_field]: value}
			})
		}
	}
}


export function testCreateComputedSetter() {
	return {
		get() {
			console.log(`getter called!`)
			return 10;
		},
		set(value) {
			console.log(`setter called! ${value} ${this.sample_id}`)
		}
	}
}