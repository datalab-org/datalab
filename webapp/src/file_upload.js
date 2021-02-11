import '@uppy/core/dist/style.css'
import '@uppy/dashboard/dist/style.css'
import Uppy from '@uppy/core'
import Dashboard from '@uppy/dashboard'
import XHRUpload from '@uppy/xhr-upload'
import Webcam from '@uppy/webcam'

import store from '@/store/index.js'

// file-upload loaded

export default function setupUppy(sample_id, trigger_selector) {
	console.log("setupUppy called with: " + trigger_selector)
	var uppy = new Uppy()
	uppy.use(Dashboard, {
		inline: false,
		trigger: trigger_selector,
	})
	.use(Webcam, {target: Dashboard})
	.use(XHRUpload, { //someday, try to upgrade this to Tus
		// headers: {'X-CSRFToken': "{{ csrf_token() }}"},
		endpoint: 'http://localhost:5001/upload-file/',
		FormData: true, // send as form 
		fieldName: 'files[]',// default, think about whether or not to change this
		showProgressDetails: true,
	})

	uppy.on('file-added', (file) => {
		uppy.setFileMeta(file.id, {
			size: file.size,
			sample_id: sample_id,
		})
	});

	uppy.on('complete', function (result) {
		console.log('Upload complete! We’ve uploaded these files:', result.successful);
		console.log('There were errors with these files:', result.failed);

		result.successful.forEach(function(f) {
			var new_filename = f.data.name;
			store.commit('addFile', {
				sample_id: sample_id,
				filename: new_filename,
			});
		});
	});
}

