import sys, re, os

import numpy as np
import warnings

STARTEND_REGEX=r'<startPosition>(\d+\.\d+)</startPosition>\s+<endPosition>(\d+\.\d+)</endPosition>'
DATA_REGEX = r'<intensities unit="counts">((-?\d+ )+-?\d+)</intensities>'

def convertSinglePattern(fn,directory=".", adjust_baseline=False, overwrite=False):
	'''converts a filename (.xrdml) to xy and writes it to directory as a .xy file.
	Does nothing (prints a message) if there is already a filename.xy in the directory'''
	fn = os.path.join(directory, fn)
	outfn = fn + ".xy"
	if os.path.exists(outfn):
		if overwrite:
			print("{} already exists in the directory {}. Overwriting.".format(outfn, directory))
		else:
			warnings.warn("{} already exists in the directory {}. rm or mv it if you wish to convert {}".format(outfn,directory,fn))
			return outfn

	with open(fn,'rU') as f:
		s = f.read()
	print("Processing file {}:".format(fn))
	start, end = getStartEnd(s)
	print("    start angle: {}    end angle: {}".format(start,end))
	intensities = getIntensities(s)

	if adjust_baseline:
		intensities = np.array(intensities)
		minI = np.min(intensities)
		if minI < 0:
			print("    adjusting baseline so that no points are negative (adding {} counts)".format(-1*np.min(intensities)))
			intensities = intensities - np.min(intensities)
		else: print("    no intensitites are less than zero, so no baseline adjustment performed")

	print("    number of datapoints: {}".format(len(intensities)))
	xystring = toXY(intensities,start,end)
	with open(outfn,'w') as of:
		of.write(xystring)
	print("    Success!")
	return outfn

def getStartEnd(s):
	'''parse a given xrdml file to find the start and end 2Theta points of the scan.
	Returns a tuple of floats: (start, end)''' 
	match = re.search(STARTEND_REGEX,s)
	if not match:
		print("the start and end 2theta positions were not found in the XML file")
		sys.exit(1)

	start = float(match.group(1))
	end = float(match.group(2))
	return start, end
	
def getIntensities(s):
	''' parses an xrdml file in string form to extract the intensities. Returns a list of floats'''
	match = re.search(DATA_REGEX,s)
	if not match: 
		print("the intensitites were not found in the XML file")
		sys.exit(1)
	out = [float(x) for x in match.group(1).split()] # the intensitites as a list of integers
	return out

def toXY(intensities,start,end):
	''' converts a given list of intensities, along with a start and end angle,
	to a string in XY format '''
	angles = np.linspace(start,end,num=len(intensities))
	xylines = ["{:.5f} {:.3f}\r\n".format(a,i) for a,i in zip(angles,intensities)]
	return "".join(xylines)