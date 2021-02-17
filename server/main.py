import os, datetime
from werkzeug.utils import secure_filename

from flask import Flask, request, jsonify, send_from_directory
from flask.json import JSONEncoder
from bson import json_util 

from flask_pymongo import PyMongo

from flask_cors import CORS

from blocks import * # the data blocks

app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})

app.config.update(
	SECRET_KEY='dummy key dont use in production',
	MONGO_URI='mongodb://localhost:27017/datalabvue',
	UPLOAD_PATH='uploads',
)


BLOCK_KINDS = { # TODO: think about autogenerating this from DataBlock's blocktype parameters
	"test": DataBlock,
	"comment": CommentBlock,
	"image":  ImageBlock,
	"xrd": XRDBlock,
	"cycle": CycleBlock,
}


# use a json encoder that can handle pymongo's bson
class CustomJSONEncoder(JSONEncoder):
	 def default(self, obj): return json_util.default(obj)
app.json_encoder = CustomJSONEncoder

mongo = PyMongo(app)
DATA_COLLECTION = mongo.db.data 

@app.route('/')
def index():
	return "This is a server"

@app.route('/new-sample/', methods=["POST"])
def create_new_sample():
	request_json = request.get_json()
	print(f"creating new samples with: {request_json}")
	sample_id = request_json["sample_id"]
	name = request_json["name"]
	date = request_json["date"]

	# check to make sure that sample_id isn't taken already
	print("Validating sample id...")
	if DATA_COLLECTION.find_one({"sample_id": sample_id}):
		print(f"Sample ID '{sample_id}' already exists in database")
		return jsonify({
			"status": "error", 
			"message":"sample_id_validation_error",
			}), 400
	print("Sample ID is unique, and can be added to the database")

	new_sample = {
		"sample_id": sample_id,
		"name": name,
		"date": date,
		"description": "",
		"blocks": [], # an array of subdocuments
		"blocks_obj": {},
		"files": [],
		"display_order": [], # an array of strings, which are ids for the blocks
	}
	
	result = DATA_COLLECTION.insert_one(new_sample)
	if not result.acknowledged:
		return jsonify(status="error", message=f"Failed to add new block to server.",
			output=result.raw_result), 400
	print("sample has been added to the database")
	return jsonify({
		"status": "success",
		"sample_list_entry": {
			"sample_id": sample_id,
			"nblocks": 0,
			"date": date,
			"name": name
		}
		}), 200

@app.route('/samples/', methods=["GET"])
def get_sample_list():
	cursor = DATA_COLLECTION.aggregate(
		[{"$project": {
			"_id":0,
			"sample_id":1,
			"nblocks":{"$size":"$display_order"},
			"date":1, 
			"chemform":1,
			"name":1
			}}]
		)
	return jsonify({
		"status":"success",
		"samples": list(cursor)
		})

@app.route('/delete-sample/', methods=["POST"])
def delete_sample():
	request_json = request.get_json()
	sample_id = request_json["sample_id"]
	print(f'received request to delete sample {sample_id}')

	result  = DATA_COLLECTION.delete_one({ "sample_id": sample_id})

	if result.deleted_count != 1:
		return jsonify({
			"status":error,
			"message": "Failed to delete sample from database"
		}), 400
	print("Deleted successfully!")
	return jsonify({
		"status":"success",		
	}), 200

@app.route('/save-sample/', methods=['POST'])
def save_sample():
	request_json = request.get_json()
	sample_id = request_json["sample_id"]
	updated_data = request_json["data"]

	del updated_data["_id"]
	updated_data["last_modified"] = datetime.datetime.now().isoformat()

	for block_id, block_data in updated_data["blocks_obj"].items():
		blocktype = block_data["blocktype"]
		Block = BLOCK_KINDS[blocktype].from_web(block_data)
		updated_data["blocks_obj"][block_id] = Block.to_db()

	print('save-sample received request\n\tsample:{}\ndata:{}'.format(sample_id, updated_data))
	result = DATA_COLLECTION.update_one(
		{"sample_id":sample_id },
		{ "$set": updated_data }
	)

	print(result.raw_result)
	if result.matched_count != 1:
		return jsonify(status="error", message=f"{blocktype} Update failed. no subdocument matched",
			output=result.raw_result), 400

	return jsonify(status="success")

@app.route('/get_sample_data/<sample_id>', methods=["GET"])
def get_sample_data(sample_id):
	# retrieve the entry from the databse:
	doc = DATA_COLLECTION.find_one_or_404({"sample_id":sample_id})
	# form = NewSampleForm(data=doc)
	# last_modified = doc["last_modified"] if "last_modified" in doc else None

	# pass all blocks through their Block objects to add any properties needed
	for block_id, block_data in doc["blocks_obj"].items():
		blocktype = block_data["blocktype"]
		Block = BLOCK_KINDS[blocktype].from_db(block_data)
		doc["blocks_obj"][block_id] = Block.to_web()

	return jsonify({
		"status": "success",
		"sample_id": sample_id,
		"sample_data": doc,
	})

# Custom static data
@app.route('/files/<sample_id>/<path:filename>')
def get_file(sample_id, filename):
	path = os.path.join(app.config['UPLOAD_PATH'], sample_id)
	print("retrieving file: {} from {}".format(filename, path))
	return send_from_directory(path, filename)

@app.route('/upload-file/', methods=["POST"])
def upload():
	'''method to upload files to the server
	todo: think more about security, size limits, and about nested folders
	'''
	print("uploaded files:")
	print(request.files)
	print(request.form)
	if len(request.files) == 0:
		return jsonify(error="No file in request"), 400
	if "sample_id" not in request.form == 0:
		return jsonify(error="No sample id provided in form"), 400
	sample_id = request.form["sample_id"]
	DATA_COLLECTION.find_one_or_404({"sample_id": sample_id}) # make sure sample_id is legit! 

	secure_sample_id = secure_filename(sample_id)
	save_path = os.path.join(app.config['UPLOAD_PATH'], secure_sample_id)
	print("secure path name: {}".format(save_path))

	for filekey in request.files: #pretty sure there is just 1 per request
		file = request.files[filekey] #just a weird thing about the request that comes from uppy. The key is "files[]"
		filename = secure_filename(file.filename)
		print("received file: {}".format(filename))
		# if filename != '':
		#    file_ext = os.path.splitext(filename)[1]
		if not os.path.exists(save_path):
			os.makedirs(save_path)
		file.save(os.path.join(save_path, filename))

		DATA_COLLECTION.update_one(
			{ "sample_id": sample_id },
			{  "$push": { "files": filename } }
		)

	return jsonify({"status":"success"}), 201

@app.route('/delete-file/', methods=["POST"])
def delete_file():
	'''delete a data file from the uploads/sample_id folder'''

	request_json = request.get_json()

	sample_id = request_json["sample_id"]
	filename = request_json["filename"]

	secure_sample_id = secure_filename(sample_id)
	secure_fname = secure_filename(filename)

	path = os.path.join(app.config["UPLOAD_PATH"], secure_sample_id, secure_fname)

	if not os.path.isfile(path):
		return jsonify(status="error", message="Delete failed. file not found: {}".format(path)), 400

	print("Deleting path: {}".format(path))
	result = DATA_COLLECTION.update_one(
		{ "sample_id": sample_id },
		{ "$pull": {"files": filename } }
	)
	print(result.raw_result)
	if result.matched_count != 1:
		return jsonify(status="error", message=f"{sample_id} {filename} delete failed. Something went wrong with the db call. File not deleted.",
			output=result.raw_result), 400

	os.remove(path)

	return jsonify({"status":"success"}), 200


# TODO: add input data validation
@app.route('/add-data-block/', methods=["POST"])
def add_data_block():
	'''Call with AJAX to add a block to the sample'''

	request_json = request.get_json()
	print("add-data-block received request:")
	print(request_json)

	# pull out required arguments from json
	sample_id = request_json["sample_id"]
	block_type = request_json["block_kind"]
	insert_index = request_json["index"]

	print(f"Adding a block of type: {block_type} to sample: {sample_id}")
	if block_type not in BLOCK_KINDS:
		return jsonify(status="error", message="Invalid block type"), 400

	block = BLOCK_KINDS[block_type](sample_id=sample_id)

	data = block.to_db()
	print("updating the database with:")
	print(sample_id)
	print(data)
	print(insert_index)

	#currently, adding to both blocks and blocks_obj to mantain compatibility with 
	# the old site. The new site only uses blocks_obj
	if insert_index:
		display_order_update = { "$each": [block.block_id], "$position":insert_index }
	else: display_order_update = block.block_id

	result = DATA_COLLECTION.update_one({"sample_id":sample_id},
		{
		"$push": { "blocks": data }, 
		"$set":  { f"blocks_obj.{block.block_id}": data},
		"$push": {	"display_order": display_order_update },
		}
	)

	print(result.raw_result)
	if result.modified_count < 1:
		return jsonify(status="error", message="Update failed. The sample_id probably incorrect: {}".format(sample_id)), 400

	# get the new display_order:
	display_order_result = DATA_COLLECTION.find_one({"sample_id":sample_id},
		{"display_order": 1})
	print("new document: {}".format(display_order_result))

	return jsonify(status="success", new_block_obj=block.to_web(), new_display_order=display_order_result["display_order"])

@app.route('/update-block/', methods=["POST"])
def update_block():
	''' Take in json block data from site, process, and spit 
	out updated data. May be used, for example, when the user 
	changes plot parameters and the server needs to generate a new 
	plot
	'''
	request_json = request.get_json()
	print("update_block called with : " + str(request_json))
	sample_id = request_json["sample_id"]
	block_id = request_json["block_id"]
	block_data = request_json["block_data"]
	blocktype = block_data["blocktype"]

	import pdb
	Block = BLOCK_KINDS[blocktype].from_web(block_data)

	return jsonify(status="success", new_block_data=Block.to_web()), 200

@app.route('/delete-block/', methods=["POST"])
def delete_block():
	'''Completely delete a data block fron the database. In the future,
	we may consider preserving data by moving it to a different array, 
	or simply making it invisible'''
	request_json = request.get_json()   
	sample_id = request_json["sample_id"]
	block_id = request_json["block_id"]

	# print(update)
	result = DATA_COLLECTION.update_one({"sample_id":sample_id},
		{
			"$pull": { 
				"blocks": { "block_id": block_id },
				"display_order": block_id,
			},
			"$unset": {f"blocks_obj.{block_id}": ""},
		})

	print("Removing block: {} , from sample: {}".format(block_id, sample_id))
	print("result:")
	print(result.raw_result)

	if result.modified_count < 1:
		return jsonify({
			"status": "error",
			"message": "Update failed. The sample_id probably incorrect: {}".format(sample_id)
			}), 400
	return jsonify({"status":"success"}), 200  # could try to switch to http 204 is "No Content" success with no json


if __name__ == '__main__':
	app.run(debug=True, port=5001)





