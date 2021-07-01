import os, random, json

import xrd_utils
import pandas as pd

from bson import ObjectId
import numpy as np
import bokeh
from bokeh.plotting import figure
from bokeh.io import curdoc
from bokeh.events import DoubleTap
from bokeh.models.callbacks import CustomJS
from simple_bokeh_plot import simple_bokeh_plot, mytheme
import bokeh_plots 
import pandas as pd
import numpy as np
from scipy.interpolate import splrep, splev
from navani import echem as ec
from file_utils import get_file_info_by_id
from scipy.signal import savgol_filter
from scipy.interpolate import splev, splrep

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
	
	defaults= {
		"p_spline": 5,  
		"s_spline": 5 ,
		"win_size_2": 101,  
		"win_size_1": 1001,
		"plotmode-dqdv": False,
		"plotmode-dvdq": False,
		

	} # values that are set by default if they are not supplied by the dictionary in init()

	def __init__(self, sample_id, dictionary={}, unique_id=None):
		self.block_id = unique_id or generate_random_id() # this is supposed to be a unique id for use in html and the database. 
		self.data = {"sample_id": sample_id, "blocktype":self.blocktype, "block_id":self.block_id, **self.defaults}

		# convert ObjectId file_ids to string to make handling them easier when sending to and from web
		if "file_id" in self.data: 
			self.data["file_id"] = str(self.data["file_id"])

		if "title" not in self.data:
			self.data["title"] = self.description
		self.data.update(dictionary) # this could overwrite blocktype and block_id. I think that's reasonable... maybe    

	def to_db(self):
		''' returns a dictionary with the data for this 
		block, ready to be input into mongodb'''
		if "file_id" in self.data:
			dict_for_db = self.data.copy() # gross, I know
			dict_for_db["file_id"] = ObjectId(dict_for_db["file_id"])
			return dict_for_db
		return self.data

	@classmethod
	def from_db(cls, db_entry):
		''' create a block from json (dictionary) stored in a db '''
		new_block = cls(db_entry["sample_id"], db_entry)
		if "file_id" in new_block.data:
			new_block.data["file_id"] = str(new_block.data["file_id"])
		return new_block

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
		if "file_id" not in self.data:
			print("XRDBlock.generate_xrd_plot(): No file set in the DataBlock")
			return None
		file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)

		filename = file_info["name"]
		ext = os.path.splitext(filename)[-1].lower()

		if ext not in [".xrdml",".xy"]:
			print("XRDBlock.generate_xrd_plot(): Unsupported file extension (must be .xrdml or .xy)")
			return None

		print(f"The XRD file to plot is found at: {file_info['location']}")
		if ext == ".xrdml":
			print("xrdml data received. converting to .xy")
			filename = xrd_utils.convertSinglePattern(file_info["location"]) # should give .xrdml.xy file
			print(f"the path is now: {filename}")
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
	

	accepted_file_extensions = ['.mpr', '.txt', '.xls', '.xlsx', '.txt', '.res']

	def parse_cycles_to_plot(cycles_string):
		''' Takes a string in the form:
			1, 2, 3-4,11
			and parses it into a list of cycle numbers

		'''
		notInt = True
		try:
			cycles_string = int(cycles_string)
			notInt = False
		except:
			print("That's not an integer number.")
			notInt = True				


		if notInt == False:
			#implies input is an integer:
			return cycles_string
				
		else:
			cycles_string = cycles_string.replace(" ", "")
			#implies input is a list
			myList = cycles_string.split(',')	#split the parts of the input into separate numbers and ranges
			print(myList)
			newList = []
			for item in myList:
				if item.find('-') == True: #check if item is range
					
					upperRange =  int(item.split("-")[1])
					lowerRange = int(item.split("-")[0])
					print(upperRange)
					myRange = []
					myRange = map(str, list(range(lowerRange, upperRange+1, 1))) #create range from 2 to 3
					
					newList.extend(myRange) # add the ints from 2 to 3 to original list

				else:
					newList.extend(item)
					continue
			
			myList = newList
			#We have no created a list of every single cycle mentioned, now convert all items to int
			myList = list(map(int, myList))
			return myList
			
	def plot_cycle(self, voltage_label='Voltage', 
			capacity_label="Capacity", 
			capacity_units='mAh'):

		if "file_id" not in self.data:
			print('No file_id given')
			return None

		file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
		filename = file_info["name"]
		ext = os.path.splitext(filename)[-1].lower()
		

		if ext not in self.accepted_file_extensions:
			print('Unrecognized filetype')
			return None

		if 'cyclenumber' not in self.data:
			self.data['cyclenumber'] = "" # plot all
		
		cycle_list = self.data['cyclenumber']
		print(type(cycle_list))
		#sspline = self.data['s_spline']
		#pspline = self.data['polynomial']
		
		#print(f'bruh {a}')
		df = ec.echem_file_loader(file_info["location"])
		print(len(df))


		def reduce_size(df):
			#Find the number of cycles, if it's greater than 10, take out every second row
			cycleNo = df['full cycle'].nunique()
			a = df['half cycle'].unique()
			a = sorted(a)
			print(a)
			for num in a:
				mydf = df.loc[df['half cycle'] == num]
				print(len(mydf))
				
				rows = len(mydf)
				indexNames = df.loc[df['half cycle'] == num].index
				#print(indexNames)
				df = df.drop(indexNames , inplace=False)
				if cycleNo >= 10:
					mydf =  bokeh_plots.reduce_df_size(mydf, rows)
				df = df.append(mydf)

			return df		
		#Function to plot normally
		def plot_norm(df,cycle_list):
			half_cycles = []  #Given input is a list of full cycles, we need to prepare list of half-cycles for detailed plotting
			print(isinstance(cycle_list, list))

			if isinstance(cycle_list, list) :  #If the input contains a list, implies not all cycles are printed so, print each half-cycle
				for item in cycle_list:
					print(item)
					half_cycles.extend([(2*item)-1, 2*item])

				for count, cycle in enumerate(cycle_list):
						idx = df[df['full cycle'] == cycle].index
						df.loc[idx, 'colour'] = count

				df = df[df['half cycle'].isin(half_cycles)]

		


			return df

		#Adapted Navani functions to help plot dqdv
		def dqdv_single_cycle(capacity, voltage, ncycle, hf_cycle,
				polynomial_spline, s_spline,
				window_size_1,
				window_size_2, polyorder_1=5,polyorder_2=5, 
				final_smooth=True):
				
			print(f"polynomial_spline  {polynomial_spline}")
			print(f"s_spline  {s_spline}")
			print(f"polyorder_1  {polyorder_1}")
			print(f"polyorder_2 {polyorder_2}")

			df = pd.DataFrame({'Capacity': capacity, 'Voltage':voltage})
			unique_v = df.astype(float).groupby('Voltage').mean().index
			unique_v_cap = df.astype(float).groupby('Voltage').mean()['Capacity']			
			x_volt = np.linspace(min(voltage), max(voltage), num=int(1e4))
			f_lit = splrep(unique_v, unique_v_cap, k=1, s=0.0)
			y_cap = splev(x_volt, f_lit)
			smooth_cap = savgol_filter(y_cap, window_size_1, polyorder_1)			
			f_smooth = splrep(x_volt, smooth_cap, k=polynomial_spline, s=s_spline)
			dqdv = splev(x_volt, f_smooth, der=1)
			mycyc = ncycle.max()
			cyc = np.full(len(x_volt), mycyc)
			
			try:
				mycyc = hf_cycle.max()
			except:
				mycyc = hf_cycle
			hf_cyc = np.full(len(x_volt), mycyc)
			#print(len(cyc))
			#print(len(x_volt))
			smooth_dqdv = savgol_filter(dqdv, window_size_2, polyorder_2)
			if final_smooth:
				return x_volt, smooth_dqdv, smooth_cap, cyc, hf_cyc
			else:
				return x_volt, dqdv, smooth_cap, cyc, hf_cyc
		def multi_dqdv_plot(df, cycle_list, 
					polynomial_spline, s_spline,
					 window_size_1,
					 window_size_2, polyorder_1 = 5,polyorder_2=5,
					capacity_label='Capacity', 
					voltage_label='Voltage',
					final_smooth=True):
					
					full_voltage_list = []
					full_dqdv_list = []
					full_cap_list = []
					full_cyc_list = []
					full_hf_cycle_list = []
					half_cycles = []
					myvoltage = []
					print(f"insidemulti {polynomial_spline}")
					for item in cycle_list:
						print(item)
						half_cycles.extend([(2*item)-1, 2*item])

					for count, cycle in enumerate(cycle_list):
						idx = df[df['full cycle'] == cycle].index
						df.loc[idx, 'colour'] = count
					print(half_cycles)

					df = df[df['half cycle'].isin(half_cycles)]
					
					for cycle in half_cycles:
						try:
							df_cycle = df[df['half cycle'] == cycle]
							print(df_cycle['full cycle'].max())
							myvoltage, dqdv, cap, f_cyc, h_cyc = dqdv_single_cycle(df_cycle[capacity_label], 
														df_cycle[voltage_label], 
														df_cycle['full cycle'],
														cycle,
														polynomial_spline = polynomial_spline,
														window_size_1=window_size_1,
														polyorder_1=polyorder_1,
														s_spline=s_spline,
														window_size_2=window_size_2,
														polyorder_2=polyorder_2,
														final_smooth=final_smooth)
							
							#print(type(full_voltage_list))
							
							

							full_voltage_list.extend(myvoltage)
							full_dqdv_list.extend(dqdv)
							full_cap_list.extend(cap)
							full_cyc_list.extend(f_cyc)
							full_hf_cycle_list.extend(h_cyc)

							
							
							
							print(f'Printed cycle number {cycle}')
						except:
							print('Tried to print unkown cycle')
					return full_voltage_list, full_dqdv_list, full_cap_list, full_cyc_list, full_hf_cycle_list
			


		#Function to plot dqdv
		def plot_dqdv(df, cycle_list, polynomial_spline, win_size_1, win_size_2,s_spline):
			if isinstance(cycle_list, list) :
				print(f"insidedqdv {polynomial_spline}")
				full_voltage_list, full_dqdv_list, full_cap_list, full_cyc_list, full_hf_cycle_list =  multi_dqdv_plot(df, cycle_list, 
							capacity_label='Capacity', 
							voltage_label='Voltage',
							polynomial_spline=polynomial_spline, s_spline=s_spline,
							window_size_1 = win_size_1, polyorder_1=5,
							window_size_2 = win_size_2, polyorder_2=5,
							final_smooth=True)

				
				print(len(full_cyc_list))
				print(len(full_cap_list))
				dict = {'Voltage': full_voltage_list, 'dqdv': full_dqdv_list, 'Capacity': full_cap_list, "full cycle": full_cyc_list, "half cycle": full_hf_cycle_list }
				final_df = pd.DataFrame(dict)
				return final_df
			else:
				cycle_list = list(df['full cycle'].unique())
				full_voltage_list, full_dqdv_list, full_cap_list, full_cyc_list, full_hf_cycle_list =  multi_dqdv_plot(df, cycle_list, 
							capacity_label='Capacity', 
							voltage_label='Voltage',
							polynomial_spline=polynomial_spline, s_spline=s_spline,
							window_size_1 = win_size_1, polyorder_1=5,
							window_size_2 = win_size_2, polyorder_2=5,
							final_smooth=True)
				
				#print(full_voltage_list)
				dict = {'Voltage': full_voltage_list, 'dqdv': full_dqdv_list, 'Capacity': full_cap_list, "full cycle": full_cyc_list, "half cycle": full_hf_cycle_list }
				final_df = pd.DataFrame(dict)
				
				
				return final_df			


			#Function to plot dqdv
		
		
		#function to plot dvdq
		def plot_dvdq(df, cycle_list, polynomial_spline, win_size_1, win_size_2,s_spline):
			if isinstance(cycle_list, list) :
				print(f"insidedqdv {polynomial_spline}")
				full_voltage_list, full_dqdv_list, full_cap_list, full_cyc_list, full_hf_cycle_list =  multi_dqdv_plot(df, cycle_list, 
							capacity_label='Voltage', 
							voltage_label='Capacity',
							polynomial_spline=polynomial_spline, s_spline=s_spline,
							window_size_1 = win_size_1, polyorder_1=5,
							window_size_2 = win_size_2, polyorder_2=5,
							final_smooth=True)

				
				print(len(full_cyc_list))
				print(len(full_cap_list))
				dict = {'Voltage': full_voltage_list, 'dqdv': full_dqdv_list, 'Capacity': full_cap_list, "full cycle": full_cyc_list, "half cycle": full_hf_cycle_list }
				final_df = pd.DataFrame(dict)
				return final_df
			else:
				cycle_list = list(df['full cycle'].unique())
				full_voltage_list, full_dqdv_list, full_cap_list, full_cyc_list, full_hf_cycle_list =  multi_dqdv_plot(df, cycle_list, 
							capacity_label='Voltage', 
							voltage_label='Capacity',
							polynomial_spline=polynomial_spline, s_spline=s_spline,
							window_size_1 = win_size_1, polyorder_1=5,
							window_size_2 = win_size_2, polyorder_2=5,
							final_smooth=True)
				
				#print(full_voltage_list)
				dict = {'Voltage': full_voltage_list, 'dqdv': full_dqdv_list, 'Capacity': full_cap_list, "full cycle": full_cyc_list, "half cycle": full_hf_cycle_list }
				final_df = pd.DataFrame(dict)
				
				
				return final_df			

				


		
			

		df = reduce_size(df)
		#Take variables from vue, assign them to these variable names 'a, b, c, d' - some of them have to be odd numbers, so that is processed
		print(f"input {self.data['p_spline']}")
		b = float(self.data['s_spline'])
		a = int(self.data['p_spline'])
		c = int(self.data['win_size_1'])
		d = int(self.data['win_size_2'])

		if (c % 2) == 0:
			c = c+1
		if (b % 2) == 0:
			b = b+1


		if self.data['plotmode-dqdv']:    
			dqdv_df = plot_dqdv(df, cycle_list,
			polynomial_spline=a, 
			s_spline= 10 ** (-b), 
			win_size_1=c, 
			win_size_2=d )
			df = plot_norm(df,cycle_list)
			
			layout = bokeh_plots.double_axes_plot_dqdv(df, dqdv_df, y_default="Voltage", )
			self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=mytheme)
		elif self.data['plotmode-dvdq']:
			dvdq_df = plot_dvdq(df, cycle_list,
			polynomial_spline=a, 
			s_spline= 10 ** (-b), 
			win_size_1=c, 
			win_size_2=d )
			df = plot_norm(df,cycle_list)
			
			





			
	def to_web(self):
		self.plot_cycle()
		return self.data

	def to_db(self):
		return { key:value for (key, value) in self.data.items() if key != "bokeh_plot_data" } # don't save the bokeh plot in the database
