import os, random, json
from simple_bokeh_plot import simple_bokeh_plot, mytheme
import xrd_utils
import bokeh
import echem as ec
from bokeh.plotting import figure

UPLOAD_PATH = "uploads"


def generate_random_id():
	'''This function generates a random 15-length string for use as an id for a datablock. It 
	should be sufficiently random that there is a negligible risk of ever generating 
	the same id twice, so this is a unique id that can be used as a unique database refrence
	and also can be used as id in the DOM. Note: uuid.uuid4() would do this too, but I think
	the generated ids are too long and ugly. 

	The ids here are HTML id friendly, using lowercase letters and numbers. The first character
	is always a letter.
	'''
	randlist = [random.choice('abcdefghijklmnopqrstuvwxyz')]+random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=14)
	return "".join(randlist)


############################################################################################################
# Resources (base classes to be extended)
############################################################################################################

class DataBlock():
	''' base class for a data block.'''

	blocktype = "generic" 
	description = "Generic Block"

	def __init__(self, sample_id, dictionary={}, unique_id=None):
		self.block_id = unique_id or generate_random_id() # this is supposed to be a unique id for use in html and the database. 
		self.data = {"sample_id": sample_id, "blocktype":self.blocktype, "block_id":self.block_id}
		if "title" not in self.data:
			self.data["title"] = self.description
		self.data.update(dictionary) # this could overwrite blocktype and block_id. I think that's reasonable... maybe    

	def to_db(self):
		''' returns a dictionary with the data for this 
		block, ready to be input into mongodb'''
		return self.data

	@classmethod
	def from_db(cls, db_entry):
		''' create a block from json (dictionary) stored in a db '''
		return cls(db_entry["sample_id"], db_entry)

	def to_web(self):
		''' returns a json-able dictionary to render the block on the web '''
		return self.data

	@classmethod
	def from_web(cls, data):
		Block = cls(data["sample_id"])
		Block.update_from_web(data)
		return Block

	def update_from_web(self, data):
		''' update the object with data received from the website. Only updates fields
		that are specified in the dictionary- other fields are left alone'''
		self.data.update(data)
		return self

class CommentBlock(DataBlock):
	blocktype = "comment"
	description = "Comment"

class ImageBlock(DataBlock):
	blocktype = "image"
	description = "Image"

class XRDBlock(DataBlock):
	blocktype="xrd"
	description="Powder XRD"

	def generate_xrd_plot(self):
		if "filename" not in self.data:
			return "No filename set in the DataBlock", ""
		filename = self.data["filename"]
		ext = os.path.splitext(filename)[-1].lower()

		if ext not in [".xrdml",".xy"]:
			return "Unsupported file extension (must be .xrdml or .xy)", ""

		directory = os.path.join(UPLOAD_PATH, self.data["sample_id"])
		print(f"The XRD file to plot is found at: {directory}")
		if ext == ".xrdml":
			print("xrdml data received. converting to .xy")
			filename = xrd_utils.convertSinglePattern(filename, directory=directory) # should give .xrdml.xy file
			print(f"the filename is now: {filename}")
		else: filename = os.path.join(directory, filename)

		p = simple_bokeh_plot(filename, x_label="2θ (°)", y_label="intensity (counts)")

		script, div = bokeh.embed.components(p, theme=mytheme)
		# self.data["bokeh_script"] = script.replace('<script type="text/javascript">','').replace('</script>','') # this isn't great...
		# self.data["bokeh_div"] = div
		self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=mytheme)

	def to_web(self):
		self.generate_xrd_plot()
		return self.data

	def to_db(self):
		return { key:value for (key, value) in self.data.items() if key != "bokeh_plot_data" } # don't save the bokeh plot in the database


class CycleBlock(DataBlock):
	blocktype="cycle"
	description="Echem cycle"
	
	accepted_files = ['.mpr', '.txt', '.xls', '.xlsx', '.txt', '.res']

	def plot_cycle(self, voltage_label='Voltage', 
			capacity_label="Capacity", 
			capacity_units='mAh'):

		if "filename" not in self.data:
			print('No filename given')
			return

		filename = self.data["filename"]
		ext = os.path.splitext(filename)[-1].lower()

		if ext not in self.accepted_files:
			print('Unrecognised filetype')
			return
		directory = os.path.join(UPLOAD_PATH, self.data["sample_id"])
		
		if 'cyclenumber' not in self.data:
			self.data['cyclenumber'] = 1
		
		cycle = self.data['cyclenumber']

		# Galvani reads in the raw MPR file then its made into a dataframe
		df = ec.echem_file_loader(os.path.join(directory, filename))
		 
		# Selecting the charge and discharge cycles from the way biologic numbers them
		# If starts with charge, change how the cycles are numbered.
		half_cycles = [(2*cycle)-1, 2*cycle]
		# output_file(output_file_) # Is this needed?
		 
		# Plotting with Bokeh!
		p = figure(plot_width=400, plot_height=400, 
						x_axis_label='Capacity / mAh', 
						y_axis_label='Voltage / V')

		# add a line renderer
		for cycle in half_cycles:
			mask = df['half cycle'] == cycle
			p.line(df[mask][capacity_label], df[mask][voltage_label])

		self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=mytheme)

	def to_web(self):
		self.plot_cycle()
		return self.data

	def to_db(self):
		return { key:value for (key, value) in self.data.items() if key != "bokeh_plot_data" } # don't save the bokeh plot in the database
