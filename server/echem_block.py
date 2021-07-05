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


from blocks import DataBlock
from file_utils import get_file_info_by_id

def reduce_size(df):
			#Find the number of cycles, if it's greater than 10, take out every second row
			number_of_cycles = df['full cycle'].nunique()
			rows = len(df)
				
			if number_of_cycles >= 10:
				df =  bokeh_plots.reduce_df_size(df, rows/2)
			

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


#Function to plot normal cycles
def plot_norm(df,cycle_list):
			half_cycles = []  #Given input is a list of full cycles, we need to prepare list of half-cycles for detailed plotting
			
			if isinstance(cycle_list, list) :  #If the input contains a list, implies not all cycles are printed so, print each half-cycle
				for item in cycle_list:
					print(item)
					half_cycles.extend([(2*item)-1, 2*item])
				for count, cycle in enumerate(cycle_list):
						idx = df[df['full cycle'] == cycle].index
						df.loc[idx, 'colour'] = count

				df = df[df['half cycle'].isin(half_cycles)]
			return df


#Function to plot dqdv
def plot_dqdv(df, cycle_list, polynomial_spline, win_size_1, win_size_2,s_spline):
			# check if there is a list of cycles
			if isinstance(cycle_list, list) :
				print(f"insidedqdv {polynomial_spline}")
				full_voltage_list, full_dqdv_list, full_cap_list, full_cyc_list, full_hf_cycle_list =  multi_dqdv_plot(df, cycle_list, 
							capacity_label='Capacity', 
							voltage_label='Voltage',
							polynomial_spline=polynomial_spline, s_spline=s_spline,
							window_size_1 = win_size_1, polyorder_1=5, #polyorders are normally 5, no difference with other values
							window_size_2 = win_size_2, polyorder_2=5,
							final_smooth=True)

				
			
				dict = {'Voltage': full_voltage_list, 'dqdv': full_dqdv_list, 'Capacity': full_cap_list, "full cycle": full_cyc_list, "half cycle": full_hf_cycle_list }
				final_df = pd.DataFrame(dict)
				return final_df
			#else print all cycles
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

#function to plot dvdq - essentially uses multi-dqdv-plot but capacity and voltage is flipped
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
		
		#User list input
		cycle_list = self.data['cyclenumber']
		
		df = ec.echem_file_loader(file_info["location"])
		print(len(df))

		#Reduce df size
		df = reduce_size(df)
		
		#Take variables from vue, assign them to these variable names 'a, b, c, d' - some of them have to be odd numbers, so that is processed
		print(f"input {self.data['p_spline']}")
		b = float(self.data['s_spline'])
		a = int(self.data['p_spline'])
		c = int(self.data['win_size_1'])
		d = int(self.data['win_size_2'])

		#c and b has to be odd
		if (c % 2) == 0:
			c = c+1
		if (b % 2) == 0:
			b = b+1

		#If user has activated dqdv mode
		if self.data['plotmode-dqdv']:    
			dqdv_df = plot_dqdv(df, cycle_list,
			polynomial_spline=a, 
			s_spline= 10 ** (-b), 
			win_size_1=c, 
			win_size_2=d )
			df = plot_norm(df, cycle_list)
			#Send to bokeh for plotting
			layout = bokeh_plots.double_axes_plot_dqdv(df, dqdv_df, y_default="Voltage", )
			self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=mytheme)
		#If user has activated dvdq mode
		elif self.data['plotmode-dvdq']:
			dvdq_df = plot_dvdq(df, cycle_list,
			polynomial_spline=a, 
			s_spline= 10 ** (-b), 
			win_size_1=c, 
			win_size_2=d )

			df = plot_norm(df, cycle_list)
			layout = bokeh_plots.double_axes_plot_dvdq(df, dvdq_df, x_default="Capacity", )
			self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=mytheme)
		#Normal plotting mode
		else:
			df = plot_norm(df, cycle_list)

			layout = bokeh_plots.selectable_axes_plot_colours(df, x_options=['Capacity', 'Voltage', 'Time',], y_options=['Capacity', 'Voltage', 'Time',])
			self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=mytheme)

			





			
	def to_web(self):
		self.plot_cycle()
		return self.data

	def to_db(self):
		return { key:value for (key, value) in self.data.items() if key != "bokeh_plot_data" } # don't save the bokeh plot in the database
