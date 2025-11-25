import os
from pathlib import Path

import bokeh.embed
import numpy as np
import pandas as pd

from bokeh.models import HoverTool, LogColorMapper, DataTable, TableColumn, BoxAnnotation, CheckboxGroup, CustomJS, Label, Range1d, Span, Select, LinearAxis, DataRange1d 
from bokeh.plotting import ColumnDataSource, figure
from bokeh.io import show
from bokeh.layouts import column, row, layout, gridplot

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER

EXCEL_LIKE_EXTENSIONS: tuple[str, ...] = (".xls", ".xlsx", ".xlsm", ".xlsb", ".odf", ".ods", ".odt")
"""A tuple of file extensions that are considered Excel-like formats."""

class GPCBlock(DataBlock):
    accepted_file_extensions = ('.xlsx',*EXCEL_LIKE_EXTENSIONS)
    blocktype = "gpc"
    name = "GPC/SEC"
    description = (
            "This block can plot GPC/SEC data from an excel file exported from Agilent GPC/SEC software "
    )

    @property
    def plot_functions(self):
        return (self.generate_gpc_plot,)

    @classmethod
    def parse_gpc_sheet(cls, filename: Path) -> pd.DataFrame:
        """Parses excel GPC/SEC data generated from Agilent GPC/SEC software

        The file consists of the following sheets: Sample Details, Raw Data, MW Results and Slice Table.
        This function reads the file, extracts retention time and response trace data from the Raw Data sheet,
        and molecular weight information from the MW Results sheet. It resturns the response trace data and
        the molecular weight data as pandas DataFrames.
        
        Args:
            filename: Path to the .xlsx file
        Returns:
            gpc: GPC/SEC dataframe with columns Retention Time (in mins) and Refractive Index (in nRIU)
            gpcmw: dataframe with columns Peaks, Mp, Mn, Mz, Mz+1, Mv, PD
            slicebounds: 2-element list containing the minimum and maximum time bounds of the slice of data used to determine the molecular weights
            npeaks: int, the number of GPC peaks identified in the slice table
            calinfo: dict, containing the calibraion information
            fminfo: dict, containing the flow rate marker information
            gpcbase: dataframe with columns Start (mins) and End (mins), and rows for the baseline regions
        """
        # Get the raw data and slice information
        gpcall = pd.read_excel(filename,sheet_name='Raw Data')
        for i in range(len(gpcall)):
            if gpcall[gpcall.columns[0]][i] == 'Raw Data':
                gpcraw = gpcall.iloc[i+2:,:]
                gpcraw = gpcraw.rename(columns=gpcall.iloc[i+1,:])
        gpcraw = gpcraw.reset_index()
        gpcslice = pd.read_excel(filename, header=1, sheet_name='Slice Table')
        npeaks = int(max(gpcslice['Peak']))
        slicebounds = []
        for i in range(npeaks):
            sliceforpeak = gpcslice[gpcslice['Peak']==i+1]
            slicebounds.append([min(sliceforpeak['RT (mins)']),max(sliceforpeak['RT (mins)'])])
        # Get information on the number and nature of response traces
        for i in range(len(gpcall)):
            if isinstance(gpcall[gpcall.columns[0]][i],str) and 'Channel Information' in gpcall[gpcall.columns[0]][i]:
                for j in range(i+2,len(gpcall)):
                    if not isinstance(gpcall[gpcall.columns[0]][j],int):
                        stopline = int(j)
                        break
                gpcchan = gpcall.iloc[i+2:stopline,:]
                gpcchan = gpcchan.rename(columns=gpcall.iloc[i+1,:])
                break
        gpcchan = gpcchan.reset_index()

        # Make a GPC data dataframe containing all the detected response traces
        gpc = pd.DataFrame()
        gpc['Retention Time'] = gpcraw['RT (mins)']
        for i in range(len(gpcchan)):
            dtype = gpcchan['Detector type'][i]
            units = gpcchan['Detector units'][i]
            gpc['{0} ({1})'.format(dtype,units)] = gpcraw['Response Trace {0}'.format(i+1)]
        #gpc = gpc.fillna(0)

        # Read the molecular weight results from the file
        gpcmw = pd.read_excel(filename, header=8,sheet_name='MW Results')
        blankind = []
        for i in range(len(gpcmw)):
            if gpcmw['Peaks'][i] == None:
                blankind.append(i)
        for i, r in gpcmw.iterrows():
            if pd.isnull(r).any():
                gpcmw.drop(i,inplace=True)
        # Get the calibration information
        gpcmwsheet = pd.read_excel(filename, sheet_name='MW Results')
        for i in range(len(gpcmwsheet['Administrative Information'])):
            if gpcmwsheet['Administrative Information'][i] == 'Column Calibration':
                gpccal = gpcmwsheet.iloc[i+1:,:2]
        gpccal=gpccal.rename(columns={'Administrative Information':'Column Calibration','Unnamed: 1':'Info'})
        gpccal = gpccal.reset_index()
        calinfo = {'Name':'','Type':'','Order':'','Coeffs':[],'Equation':'','RTlims':[],'MWlims':[]}
        for i in range(len(gpccal)):
            if gpccal['Column Calibration'][i] == 'Name':
                calinfo['Name'] = gpccal['Info'][i]
            if gpccal['Column Calibration'][i] == 'Curve Fit Type':
                calinfo['Type'] = gpccal['Info'][i]
            if gpccal['Column Calibration'][i] == 'Order Of Curve Fit':
                calinfo['Order'] = gpccal['Info'][i]
            if 'Coeff ' in gpccal['Column Calibration'][i]:
                calinfo['Coeffs'].append(gpccal['Info'][i])
            if gpccal['Column Calibration'][i] == 'Curve Fit Equation':
                calinfo['Equation'] = gpccal['Info'][i]
            if 'Limit RT (mins)' in gpccal['Column Calibration'][i]:
                calinfo['RTlims'].append(gpccal['Info'][i])
            if 'Limit MW' in gpccal['Column Calibration'][i]:
                calinfo['MWlims'].append(gpccal['Info'])
        # Get the flow rate marker information
        for i in range(len(gpcmwsheet['Administrative Information'])):
            if gpcmwsheet['Administrative Information'][i] == 'Flowrate Information':
                gpcflow = gpcmwsheet.iloc[i+1:i+3,:2]
        gpcflow=gpcflow.rename(columns={'Administrative Information':'Flowrate Information','Unnamed: 1':'Info'})
        gpcflow = gpcflow.reset_index()
        fminfo = {'Name':'','RT':'','FRCF':''}
        for i in range(len(gpcflow)):
            if gpcflow['Flowrate Information'][i] == 'FRM Name':
                fminfo['Name'] = gpcflow['Info'][i]
            if gpcflow['Flowrate Information'][i] == 'FRM RT (mins)':
                fminfo['RT'] = gpcflow['Info'][i]
            if gpcflow['Flowrate Information'][i] == 'FRCF':
                fminfo['FRCF'] = gpcflow['Info'][i]
        # Get the baseline information
        for i in range(len(gpcmwsheet['Administrative Information'])):
            if gpcmwsheet['Administrative Information'][i] == 'Baseline regions':
                for j in range(i,len(gpcmwsheet)):
                    if not isinstance(gpcmwsheet['Administrative Information'][j],str):
                        stopline = int(j)
                        break
                gpcbase = gpcmwsheet.iloc[i:stopline,:3]
                break
        gpcbase.columns = gpcbase.iloc[0]
        gpcbase = gpcbase[1:]
        gpcbase = gpcbase.reset_index()

        return gpc, gpcmw, slicebounds, npeaks, calinfo, fminfo, gpcbase


    @classmethod
    def _format_gpc_plot(self, gpc_data: pd.DataFrame,mwdata: pd.DataFrame,slicebounds: list,npeaks:int,calinfo:dict,fminfo:dict,gpcbase:pd.DataFrame) -> bokeh.layouts.layout:
        """Formats GPC/SEC data from plotting in Bokeh, with vertical lines to indicate the slice of data
        that was used to determine the molecular weights

        Args:
            gpc_data (pd.DataFrame): GPC/SEC data with columns "Retention Time" and "Refractive Index (nIRU)"
            mwdata (pd.DataFrame): molecular weight data with columns "Peaks", "Mp", "Mn", "Mz", "Mz+1", "Mv", "PD"
            slicebounds (list): 2-element list containing the minimum and maximum time bounds of the slice of data used to determine the molecular weights
            npeaks (int): The number of GPC peaks identified in the slice table
            calinfo (dict): dictionary containing information on the calibration: its name, functional form, order, coefficients, and equation
            fminfo (dict): dictionary containing information on the flow rate marker: its name, RT (mins) and FRCF
            gpcbase (pd.DataFrame): columns for Start (mins) and End (mins) of each baseline region indicated in the file

        Returns:
            bokeh.layouts.layout: Bokeh layout with GPC/SEC data plotted and MW data in a table
        """
        # Call the pydatalab selectable_axes_plot function for the actual data
        plotlayout = selectable_axes_plot(
            gpc_data,
            x_options=["Retention Time"],    # Fix X axis option
            y_options=list(gpc_data)[1:],  # Y axis options are the response traces
            y_default=list(gpc_data)[1],
            color_mapper=LogColorMapper("Cividis256"),
            plot_points=False,   # Only lines for the response trace
            plot_line=True,  # Line should be plotted
            show_table=False,
            tools=HoverTool(
                tooltips=[
                    ("Retention Time /min","$x"),
                    ("Refractive Index /nRIU","$y"),
                ],
                mode="vline",
            ),
        )
        # Adding min to the x-axis label 
        plotlayout.children[1].xaxis.axis_label = "Retention Time /min"
        
        # Make a bonus y axis for a second response trace
        # Checkbox for bonus y axis
        bonusymenu = ['None']
        bonusymenu += list(gpc_data)[1:]
        bonusyselect = Select(title='Second y axis?',value='None',options=bonusymenu,height_policy='min')
        # The bonus axis
        bonusy = []
        bonusplot = []
        plotlayout.children[1].extra_y_ranges = {}
        for i in range(1,len(bonusymenu)):
            renderersource = ColumnDataSource(gpc_data)
            plotlayout.children[1].extra_y_ranges["y{0}".format(i)] = DataRange1d(renderers=[\
                    plotlayout.children[1].line(source=renderersource,\
                                                        x=list(gpc_data)[0],\
                                                        y=bonusymenu[i],\
                                                        visible=False)])
            bonusy.append(LinearAxis(y_range_name="y{0}".format(i),\
                                    axis_label=bonusymenu[i],\
                                    axis_label_text_color='red',\
                                    major_label_text_color='red',\
                                    visible=False))
            bonusplot.append(plotlayout.children[1].line(gpc_data[list(gpc_data)[0]],\
                                                    gpc_data[bonusymenu[i]],\
                                                    y_range_name="y{0}".format(i),\
                                                    color='red',\
                                                    visible=False))
            plotlayout.children[1].add_layout(bonusy[i-1],'right')

        bonusyselect.js_on_change('value',CustomJS(args=dict(bonusy=bonusy,\
                                                            bonusymenu=bonusymenu,\
                                                            bonusplot=bonusplot),\
                                code = """
            for (let axcount = 0; axcount < bonusy.length; axcount++) {
                if (cb_obj.value == bonusymenu[axcount+1]) {
                    bonusy[axcount].visible = true
                    bonusplot[axcount].visible = true
                    }
                else {
                    bonusy[axcount].visible = false
                    bonusplot[axcount].visible = false
                    }
                }
            """
            ))

        # Add shaded areas for the peaks in the slice table
        # Check whether to show the slices    
        prodcheckbox = CheckboxGroup(labels=['Show slice regions?','Show baseline regions?','Show flow rate marker information?'],\
                active=[0,1],\
                height_policy='min')
        # Actually show the slices
        shades = []
        for i in range(npeaks):
            if i % 2 == 0:
                shadecol = 'blue'
                hatchpat = '/'
            else:
                shadecol = 'red'
                hatchpat = '\\'
            shades.append(BoxAnnotation(left=slicebounds[i][0],right=slicebounds[i][1],fill_color=shadecol,\
                    fill_alpha=0.1,hatch_pattern=hatchpat,hatch_alpha=0.1,level='underlay',\
                    line_color='grey',line_alpha=0.1,visible=True))
            plotlayout.children[1].add_layout(shades[i])

        # Add a line for the flowrate marker to the plot
        if fminfo['Name'] != '' and fminfo['RT'] != 0:
            flowmark = Span(location=float(fminfo['RT']),dimension='height',line_color='grey',level='underlay',visible=False)
            flowmarklab = Label(text='Flow rate marker\n{0}'.format(fminfo['Name']),\
                    x=fminfo['RT'],border_line_color='black',background_fill_color='white',visible=False)
        else:
            flowmark =  Span(location=float(fminfo['RT']),dimension='height',line_color='white',level='underlay',line_alpha=0,visible=False)
            flowmarklab = Label(text='Flow rate marker info\nnot given in file',\
                        border_line_color='black',\
                        background_fill_color='white',visible=False)
        plotlayout.children[1].add_layout(flowmark)
        plotlayout.children[1].add_layout(flowmarklab)

        # Add shaded regions for the baseline
        baseshades = []
        for i in range(len(gpcbase)):
            baseshades.append(BoxAnnotation(left=gpcbase['Start (mins)'][i],\
                    right=gpcbase['End (mins)'][i],
                    fill_color='grey',\
                            fill_alpha=0.2,\
                            level='underlay',visible=True))
            plotlayout.children[1].add_layout(baseshades[i])

        # Use checkboxes to toggle plot elements on and off for main plot
        toggleable = {'shades':shades,\
                'flowmark':flowmark,\
                'flowmarklab':flowmarklab,\
                'baseshades':baseshades,\
                'prodcheckbox':'prodcheckbox'}
        prodcheckbox.js_on_click(CustomJS(args=toggleable,code = """
            for (let shadecount = 0; shadecount < shades.length; shadecount++) {
                shades[shadecount].visible = cb_obj.active.includes(0)
                }
            for (let bshadecount = 0; bshadecount < baseshades.length; bshadecount++) {
                baseshades[bshadecount].visible = cb_obj.active.includes(1)
                }
            flowmark.visible = cb_obj.active.includes(2)
            flowmarklab.visible = cb_obj.active.includes(2)
            """
            ))

        table = DataTable(
            source=ColumnDataSource(mwdata), 
            columns=[TableColumn(field=c) for c in mwdata.columns.to_list()],\
                    sizing_mode='stretch_width',\
                    height=50+25*len(mwdata)
            )

        # Checkbox for whether to show calibration curve
        calcheckbox = CheckboxGroup(labels=['Show calibration curve?'],active=[0],sizing_mode='stretch_width')

        # Plot the calibration curve
        if len(calinfo['RTlims']) > 0:
            xlims = list(calinfo['RTlims'])
            callims = 'yes'
        else:
            xlims = [min(gpc_data['Retention Time']),max(gpc_data['Retention Time'])]
            callims = 'no'
        x_cal = np.linspace(min(xlims),max(xlims))
        y_cal = np.zeros(len(x_cal,))
        if calinfo['Type'] == 'Polynomial':
            for i in range(len(x_cal)):
                pointx = x_cal[i]
                pointy = 0
                for j in range(len(calinfo['Coeffs'])):
                    pointy += pow(pointx,j)*calinfo['Coeffs'][j]
                y_cal[i] = pointy
            calnums = pd.DataFrame()
            calnums['Retention Time /min'] = x_cal
            calnums['log₁₀(Molecular Weight)'] = y_cal
            callayout = selectable_axes_plot(
                calnums,
                x_options=['Retention Time /min'],
                y_options=['log₁₀(Molecular Weight)'],
                color_mapper=LogColorMapper("Cividis256"),
                plot_points=False,   # Plot line only 
                plot_line=True,  # Line should be plotted
                show_table=False,
                tools=HoverTool(
                tooltips=[
                    ("Retention Time /min","$x"),
                    ('log₁₀(Molecular Weight)',"$y"),
                ],
                mode="vline",
               )
                )
            if callims == 'yes':
                labeltext = 'Calibration curve \nName {0}\n{1}\nCalibration from {2} to {3} mins'.format(calinfo['Name'],calinfo['Equation'],round(min(x_cal),2),round(max(x_cal),2))
            else:
                labeltext = 'Calibration curve \nName {0}\n{1}\nWarning: limits of calibration not given in file'.format(calinfo['Name'],calinfo['Equation'])
            label = Label(text=labeltext,\
                    border_line_color='black',\
                    background_fill_color='white',\
                    x=min(x_cal),y=min(y_cal))
            callayout.children[1].add_layout(label)
        else:
            callayout = figure(sizing_mode='scale_width',aspect_ratio=1.5,\
                    x_axis_label= "Retention Time /min",\
                    y_axis_label='log₁₀(Molecular Weight)')
            callayout.x_range = Range1d(min(gpc_data['Retention Time']),max(gpc_data['Retention Time']))
            callayout.y_range = Range1d(0,10)
            label = Label(text='Calibration curve\nName {0}\n{1}\nPlotting for this functional form not currently supported'.format(calinfo['Name'],calinfo['Equation']),\
                    border_line_color='black',\
                    background_fill_color='white')
            callayout.add_layout(label)
        callayout.visible=True

        # Put everything together in a bokeh layout
        fulllayout = gridplot(
                children=[
                    [plotlayout],
                    [bonusyselect],
                    [prodcheckbox],
                    [table],
                    [calcheckbox],
                    [callayout],
                   ],
                sizing_mode='stretch_both',
                )
        
        calcheckbox.js_on_click(CustomJS(args=dict(\
                callayout=callayout,\
                calcheckbox=calcheckbox),\
                code = """
            callayout.visible=0 in calcheckbox.active
            """))

        return fulllayout

    def generate_gpc_plot(self):
        file_info = None
        gpc_data = None

        if "file_id" not in self.data:
            LOGGER.warning("No file set in the DataBlock")
            return
        else:
            file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
            ext = os.path.splitext(file_info["location"].split("/")[-1])[-1].lower()
            if ext not in self.accepted_file_extensions:
                LOGGER.warning(
                    "Unsupported file extension (must be one of %s, not %s)",
                    self.accepted_file_extensions,
                    ext,
                )
                return
            
            gpc_data, gpcmw, slicebounds, npeaks, calinfo, fminfo, gpcbase = self.parse_gpc_sheet(Path(file_info["location"]))

        self.data["npeaks"] = len(gpcmw)
        for i in range(len(gpcmw)):
            for column in gpcmw.columns[1:]:
                print(column)
                self.data["{0} Peak {1}".format(column,i+1)] = float(gpcmw[column][i])
        
        if gpc_data is not None:
            fulllayout = self._format_gpc_plot(gpc_data,gpcmw,slicebounds,npeaks,calinfo,fminfo,gpcbase)
            self.data["bokeh_plot_data"] = bokeh.embed.json_item(fulllayout, theme=DATALAB_BOKEH_THEME)

