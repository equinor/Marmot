# -*- coding: utf-8 -*-
"""
Created on Tue Jan 14 07:42:06 2020

This module creates unserved energy timeseries line plots and total bat plots and is called from marmot_plot_main.py

@author: dlevie
"""

import pandas as pd
import matplotlib as mpl
import logging
import marmot.plottingmodules.marmot_plot_functions as mfunc
import marmot.config.mconfig as mconfig

#===============================================================================

class MPlot(object):
    def __init__(self, argument_dict):
        # iterate over items in argument_dict and set as properties of class
        # see key_list in Marmot_plot_main for list of properties
        for prop in argument_dict:
            self.__setattr__(prop, argument_dict[prop])

        self.logger = logging.getLogger('marmot_plot.'+__name__)
        self.y_axes_decimalpt = mconfig.parser("axes_options","y_axes_decimalpt")
        self.mplot_data_dict = {}


    def unserved_energy_timeseries(self, figure_name=None, prop=None, start=None, end=None, 
                  timezone="", start_date_range=None, end_date_range=None):

        outputs = {}
        
        if self.AGG_BY == 'zone':
            agg = 'zone'
        else:
            agg = 'region'
            
        # List of properties needed by the plot, properties are a set of tuples and contain 3 parts:
        # required True/False, property name and scenarios required, scenarios must be a list.
        properties = [(True, f"{agg}_Unserved_Energy", self.Scenarios)]
        
        # Runs get_data to populate mplot_data_dict with all required properties, returns a 1 if required data is missing
        check_input_data = mfunc.get_data(self.mplot_data_dict, properties,self.Marmot_Solutions_folder)

        if 1 in check_input_data:
            return mfunc.MissingInputData()
        
        for zone_input in self.Zones:
            self.logger.info(f'Zone = {zone_input}')
            Unserved_Energy_Timeseries_Out = pd.DataFrame()

            for scenario in self.Scenarios:
                self.logger.info(f'Scenario = {scenario}')

                unserved_eng_timeseries = self.mplot_data_dict[f"{agg}_Unserved_Energy"].get(scenario)
                unserved_eng_timeseries = unserved_eng_timeseries.xs(zone_input,level=self.AGG_BY)
                unserved_eng_timeseries = unserved_eng_timeseries.groupby(["timestamp"]).sum()
####################################################################
# Unable to test due to lack of data
                # if pd.isna(start_date_range) == False:
                #     self.logger.info(f"Plotting specific date range: \
                #                       {str(start_date_range)} to {str(end_date_range)}")
                #     unserved_eng_timeseries = unserved_eng_timeseries[start_date_range : end_date_range]
######################################################################
                unserved_eng_timeseries = unserved_eng_timeseries.squeeze() #Convert to Series
                unserved_eng_timeseries.rename(scenario, inplace=True)
                Unserved_Energy_Timeseries_Out = pd.concat([Unserved_Energy_Timeseries_Out, unserved_eng_timeseries], axis=1, sort=False).fillna(0)

            Unserved_Energy_Timeseries_Out.columns = Unserved_Energy_Timeseries_Out.columns.str.replace('_',' ')
            Unserved_Energy_Timeseries_Out = Unserved_Energy_Timeseries_Out.loc[:, (Unserved_Energy_Timeseries_Out >= 1).any(axis=0)]

            # correct sum for non-hourly runs
            interval_count = mfunc.get_sub_hour_interval_count(Unserved_Energy_Timeseries_Out)
            Unserved_Energy_Timeseries_Out = Unserved_Energy_Timeseries_Out/interval_count

            if Unserved_Energy_Timeseries_Out.empty==True:
                self.logger.info(f'No Unserved Energy in {zone_input}')
                out = mfunc.MissingZoneData()
                outputs[zone_input] = out
                continue
            
            # Determine auto unit coversion
            unitconversion = mfunc.capacity_energy_unitconversion(Unserved_Energy_Timeseries_Out.values.max())
            Unserved_Energy_Timeseries_Out = Unserved_Energy_Timeseries_Out/unitconversion['divisor'] 
            
            # Data table of values to return to main program
            Data_Table_Out = Unserved_Energy_Timeseries_Out.add_suffix(f" ({unitconversion['units']})")
            
            fig1, axs = mfunc.setup_plot()
            #flatten object
            ax = axs[0]
            # Converts color_list into an iterable list for use in a loop
            iter_colour = iter(self.color_list)

            for column in Unserved_Energy_Timeseries_Out:
                ax.plot(Unserved_Energy_Timeseries_Out[column], linewidth=3, antialiased=True,
                         color=next(iter_colour), label=column)
                ax.legend(loc='lower left',bbox_to_anchor=(1,0),
                          facecolor='inherit', frameon=True)
            ax.set_ylabel(f"Unserved Energy ({unitconversion['units']})",  color='black', rotation='vertical')
            ax.set_ylim(bottom=0)
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.tick_params(axis='y', which='major', length=5, width=1)
            ax.tick_params(axis='x', which='major', length=5, width=1)
            ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x, p: format(x, f',.{self.y_axes_decimalpt}f')))
            ax.margins(x=0.01)
            mfunc.set_plot_timeseries_format(axs)
            if mconfig.parser("plot_title_as_region"):
                ax.set_title(zone_input)
            outputs[zone_input] = {'fig': fig1, 'data_table': Data_Table_Out}

        return outputs


    def tot_unserved_energy(self, figure_name=None, prop=None, start=None, end=None, 
                  timezone="", start_date_range=None, end_date_range=None):
        outputs = {}
        
        if self.AGG_BY == 'zone':
            agg = 'zone'
        else:
            agg = 'region'
            
        # List of properties needed by the plot, properties are a set of tuples and contain 3 parts:
        # required True/False, property name and scenarios required, scenarios must be a list.
        properties = [(True, f"{agg}_Unserved_Energy", self.Scenarios)]
        
        # Runs get_data to populate mplot_data_dict with all required properties, returns a 1 if required data is missing
        check_input_data = mfunc.get_data(self.mplot_data_dict, properties,self.Marmot_Solutions_folder)

        if 1 in check_input_data:
            return mfunc.MissingInputData()

        for zone_input in self.Zones:
            Unserved_Energy_Timeseries_Out = pd.DataFrame()
            Total_Unserved_Energy_Out = pd.DataFrame()
            self.logger.info(f"{self.AGG_BY} = {zone_input}")
            
            for scenario in self.Scenarios:
                self.logger.info(f'Scenario = {scenario}')

                unserved_eng_timeseries = self.mplot_data_dict[f"{agg}_Unserved_Energy"].get(scenario)
                unserved_eng_timeseries = unserved_eng_timeseries.xs(zone_input,level=self.AGG_BY)
                unserved_eng_timeseries = unserved_eng_timeseries.groupby(["timestamp"]).sum()
####################################################################
# Unable to test due to lack of data
                # if pd.isna(start_date_range) == False:
                #     self.logger.info(f"Plotting specific date range: \
                #                       {str(start_date_range)} to {str(end_date_range)}")
                #     unserved_eng_timeseries = unserved_eng_timeseries[start_date_range : end_date_range]
######################################################################
                unserved_eng_timeseries = unserved_eng_timeseries.squeeze() #Convert to Series
                unserved_eng_timeseries.rename(scenario, inplace=True)
                                
                Unserved_Energy_Timeseries_Out = pd.concat([Unserved_Energy_Timeseries_Out, unserved_eng_timeseries], axis=1, sort=False).fillna(0)

            Unserved_Energy_Timeseries_Out.columns = Unserved_Energy_Timeseries_Out.columns.str.replace('_',' ')

            # correct sum for non-hourly runs
            interval_count = mfunc.get_sub_hour_interval_count(Unserved_Energy_Timeseries_Out)
            Unserved_Energy_Timeseries_Out = Unserved_Energy_Timeseries_Out/interval_count

            Total_Unserved_Energy_Out.index = Total_Unserved_Energy_Out.index.str.replace('_',' ')
            Total_Unserved_Energy_Out, angle = mfunc.check_label_angle(Total_Unserved_Energy_Out, True)
            Total_Unserved_Energy_Out = Unserved_Energy_Timeseries_Out.sum(axis=0)
            Total_Unserved_Energy_Out = pd.DataFrame(Total_Unserved_Energy_Out.T)

            if Total_Unserved_Energy_Out.values.sum() == 0:
                self.logger.info(f'No Unserved Energy in {zone_input}')
                out = mfunc.MissingZoneData()
                outputs[zone_input] = out
                continue
            
            # Determine auto unit coversion
            unitconversion = mfunc.capacity_energy_unitconversion(Total_Unserved_Energy_Out.values.max())
            Total_Unserved_Energy_Out = Total_Unserved_Energy_Out/unitconversion['divisor']
            
            # Data table of values to return to main program
            Data_Table_Out = Total_Unserved_Energy_Out.add_suffix(f" ({unitconversion['units']})")
            
            # create color dictionary
            color_dict = dict(zip(Total_Unserved_Energy_Out.index,self.color_list))
            fig2, axs = mfunc.setup_plot()
            #flatten object
            ax=axs[0]
            
            mfunc.create_bar_plot(Total_Unserved_Energy_Out.T,ax,color_dict,angle)
            ax.set_ylabel(f"Total Unserved Energy ({unitconversion['units']}h)",  color='black', rotation='vertical')
            ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x, p: format(x, f',.{self.y_axes_decimalpt}f')))
            ax.xaxis.set_visible(False)
            ax.margins(x=0.01)
            if angle > 0:
                ax.set_xticklabels(Total_Unserved_Energy_Out.columns, ha="right")
                tick_length = 8
            else:
                tick_length = 5
            ax.tick_params(axis='y', which='major', length=tick_length, width=1)
            ax.tick_params(axis='x', which='major', length=tick_length, width=1)
            ax.legend(loc='lower left',bbox_to_anchor=(1,0),
                          facecolor='inherit', frameon=True)
            if mconfig.parser("plot_title_as_region"):
                ax.set_title(zone_input)  
            for patch in ax.patches:
                width, height = patch.get_width(), patch.get_height()
                if height<=1:
                    continue
                x, y = patch.get_xy()
                ax.text(x+width/2,
                    y+height/2,
                    '{:,.1f}'.format(height),
                    horizontalalignment='center',
                    verticalalignment='center', fontsize=13)

            outputs[zone_input] = {'fig': fig2, 'data_table': Data_Table_Out}

        return outputs


    def average_diurnal_ue(self, figure_name=None, prop=None, start=None, end=None, 
                  timezone=None, start_date_range=None, end_date_range=None):
        """average diurnal unserved energy line plot"""
        
        outputs = {}
        
        if self.AGG_BY == 'zone':
            agg = 'zone'
        else:
            agg = 'region'
        
        # List of properties needed by the plot, properties are a set of tuples and contain 3 parts:
        # required True/False, property name and scenarios required, scenarios must be a list.
        properties = [(True,f"{agg}_Unserved_Energy",self.Scenarios)]
        
        # Runs get_data to populate mplot_data_dict with all required properties, returns a 1 if required data is missing
        check_input_data = mfunc.get_data(self.mplot_data_dict, properties,self.Marmot_Solutions_folder)

        if 1 in check_input_data:
            return mfunc.MissingInputData()

        for zone_input in self.Zones:
            self.logger.info(f"{self.AGG_BY} = {zone_input}")
            
            Unserved_Energy_Out = pd.DataFrame()
            #PV_Curtailment_DC = pd.DataFrame()
            
            for scenario in self.Scenarios:
                self.logger.info(f"Scenario = {scenario}")
                
                Unserved_Energy = self.mplot_data_dict[f"{agg}_Unserved_Energy"][scenario]
                try:
                    Unserved_Energy = Unserved_Energy.xs(zone_input,level=self.AGG_BY)
                except KeyError:
                    self.logger.info(f'No unserved energy in {zone_input}')
                
                Unserved_Energy = Unserved_Energy.groupby(["timestamp"]).sum()
                Unserved_Energy = Unserved_Energy.squeeze()

                if pd.isna(start_date_range) == False:
                    self.logger.info(f"Plotting specific date range: \
                    {str(start_date_range)} to {str(end_date_range)}")
                    Unserved_Energy = Unserved_Energy[start_date_range : end_date_range]
                    #pv_curt = pv_curt[start_date_range : end_date_range]
                    
                    if Unserved_Energy.empty is True: 
                        self.logger.warning('No data in selected Date Range')
                        continue
                    
                Unserved_Energy = Unserved_Energy.groupby([Unserved_Energy.index.floor('d')]).sum()
                interval_count = mfunc.get_sub_hour_interval_count(Unserved_Energy)
                Unserved_Energy = Unserved_Energy*interval_count
            
                Unserved_Energy.rename(scenario, inplace=True)

                Unserved_Energy_Out = pd.concat([Unserved_Energy_Out, Unserved_Energy], axis=1, sort=False)

            # Remove columns that have values less than 1
            #Unserved_Energy_Out = Unserved_Energy_Out.loc[:, (Unserved_Energy_Out >= 1).any(axis=0)]

            # Replace _ with white space
            Unserved_Energy_Out.columns = Unserved_Energy_Out.columns.str.replace('_',' ')

            # Create Dictionary from scenario names and color list
            colour_dict = dict(zip(Unserved_Energy_Out.columns, self.color_list))

            fig, axs = mfunc.setup_plot()
            # flatten object
            ax = axs[0]

            unitconversion = mfunc.capacity_energy_unitconversion(Unserved_Energy_Out.values.max())
            Unserved_Energy_Out = Unserved_Energy_Out / unitconversion['divisor']
            Data_Table_Out = Unserved_Energy_Out
            Data_Table_Out = Data_Table_Out.add_suffix(f" ({unitconversion['units']})")
            
            for column in Unserved_Energy_Out:
                ax.plot(Unserved_Energy_Out[column], linewidth=3, color=colour_dict[column],
                        label=column)
                ax.legend(loc='lower left',bbox_to_anchor=(1,0),
                          facecolor='inherit', frameon=True)
                ax.set_ylabel(f"Unserved Energy ({unitconversion['units']})",  color='black', rotation='vertical')
            
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.tick_params(axis='y', which='major', length=5, width=1)
            ax.tick_params(axis='x', which='major', length=5, width=1)
            ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x, p: format(x, f',.{self.y_axes_decimalpt}f')))
            ax.margins(x=0.01)
            mfunc.set_plot_timeseries_format(axs)
            ax.set_ylim(bottom=0)
            if mconfig.parser("plot_title_as_region"):
                ax.set_title(zone_input)

            outputs[zone_input] = {'fig': fig, 'data_table': Data_Table_Out}
        return outputs
