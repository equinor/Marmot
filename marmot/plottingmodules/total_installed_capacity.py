# -*- coding: utf-8 -*-
"""Generato total installed capacity plots.

This module plots figures of the total installed capacity of the system.
This
@author: Daniel Levie
"""

import os
import re
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Patch

import marmot.plottingmodules.total_generation as gen
import marmot.config.mconfig as mconfig
from marmot.plottingmodules.plotutils.plot_data_helper import PlotDataHelper
from marmot.plottingmodules.plotutils.plot_exceptions import (MissingInputData, MissingZoneData)


custom_legend_elements = Patch(facecolor='#DD0200',
                               alpha=0.5, edgecolor='#DD0200')

class MPlot(PlotDataHelper):
    """total_installed_capacity MPlot class.

    All the plotting modules use this same class name.
    This class contains plotting methods that are grouped based on the
    current module name.
    
    The total_installed_capacity module contains methods that are
    related to the total installed capacity of generators and other devices. 

    MPlot inherits from the PlotDataHelper class to assist in creating figures.    
    """

    def __init__(self, argument_dict: dict):
        """
        Args:
            argument_dict (dict): Dictionary containing all
                arguments passed from MarmotPlot.
        """
        # iterate over items in argument_dict and set as properties of class
        # see key_list in Marmot_plot_main for list of properties
        for prop in argument_dict:
            self.__setattr__(prop, argument_dict[prop])

        # Instantiation of MPlotHelperFunctions
        super().__init__(self.Marmot_Solutions_folder, self.AGG_BY, self.ordered_gen, 
                    self.PLEXOS_color_dict, self.Scenarios, self.ylabels, 
                    self.xlabels, self.gen_names_dict, Region_Mapping=self.Region_Mapping) 

        # used for combined cap/gen plot
        self.argument_dict = argument_dict
        self.logger = logging.getLogger('marmot_plot.'+__name__)
        self.x = mconfig.parser("figure_size","xdimension")
        self.y = mconfig.parser("figure_size","ydimension")
        self.y_axes_decimalpt = mconfig.parser("axes_options","y_axes_decimalpt")
        

    def total_cap(self, **_):
        """Creates a stacked barplot of total installed capacity.

        Each sceanrio will be plotted as a separate bar.

        Returns:
            dict: Dictionary containing the created plot and its data table.
        """
        outputs = {}
        # List of properties needed by the plot, properties are a set of tuples and contain 3 parts:
        # required True/False, property name and scenarios required, scenarios must be a list.
        properties = [(True, "generator_Installed_Capacity", self.Scenarios)]

        # Runs get_data to populate mplot_data_dict with all required properties,
        # returns a 1 if required data is missing
        check_input_data = self.get_formatted_data(properties)

        # Checks if all data required by plot is available, if 1 in list required data is missing
        if 1 in check_input_data:
            outputs = MissingInputData()
            return outputs

        for zone_input in self.Zones:
            Total_Installed_Capacity_Out = pd.DataFrame()
            self.logger.info(f"{self.AGG_BY} = {zone_input}")

            for scenario in self.Scenarios:

                self.logger.info(f"Scenario = {scenario}")

                Total_Installed_Capacity = self["generator_Installed_Capacity"].get(scenario)

                zones_with_cap = Total_Installed_Capacity.index.get_level_values(self.AGG_BY).unique()
                if scenario == 'ADS':
                    zone_input_adj = zone_input.split('_WI')[0]
                else:
                    zone_input_adj = zone_input
                if zone_input_adj in zones_with_cap:
                    Total_Installed_Capacity = Total_Installed_Capacity.xs(zone_input_adj, level=self.AGG_BY)
                else:
                    self.logger.warning(f"No installed capacity in {zone_input}")
                    outputs[zone_input] = MissingZoneData()
                    continue

                Total_Installed_Capacity = self.df_process_gen_inputs(Total_Installed_Capacity)
                Total_Installed_Capacity.reset_index(drop=True, inplace=True)
                Total_Installed_Capacity.rename(index={0: scenario}, inplace=True)
                Total_Installed_Capacity_Out = pd.concat([Total_Installed_Capacity_Out,
                                                          Total_Installed_Capacity],
                                                         axis=0, sort=False).fillna(0)

            Total_Installed_Capacity_Out = Total_Installed_Capacity_Out.loc[:, (Total_Installed_Capacity_Out != 0).any(axis=0)]

            # If Total_Installed_Capacity_Out df is empty returns a empty dataframe and does not plot
            if Total_Installed_Capacity_Out.empty:
                self.logger.warning(f"No installed capacity in {zone_input}")
                out = MissingZoneData()
                outputs[zone_input] = out
                continue

            unitconversion = PlotDataHelper.capacity_energy_unitconversion(max(Total_Installed_Capacity_Out.sum()))
            Total_Installed_Capacity_Out = Total_Installed_Capacity_Out/unitconversion['divisor']

            Data_Table_Out = Total_Installed_Capacity_Out
            Data_Table_Out = Data_Table_Out.add_suffix(f" ({unitconversion['units']})")

            Total_Installed_Capacity_Out.index = Total_Installed_Capacity_Out.index.str.replace('_', ' ')
            
            fig1, ax = plt.subplots(figsize=(self.x, self.y))

            Total_Installed_Capacity_Out.plot.bar(stacked=True, ax=ax,
                                                  color=[self.PLEXOS_color_dict.get(x, '#333333') 
                                                         for x in Total_Installed_Capacity_Out.columns],
                                                  edgecolor='black', linewidth='0.1')

            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.set_ylabel(f"Total Installed Capacity ({unitconversion['units']})",
                          color='black', rotation='vertical')
            ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(
                                         lambda x, p: format(x, f',.{self.y_axes_decimalpt}f')))
            
            # Set x-tick labels
            if len(self.custom_xticklabels) > 1:
                tick_labels = self.custom_xticklabels
            else:
                tick_labels = Total_Installed_Capacity_Out.index
            PlotDataHelper.set_barplot_xticklabels(tick_labels, ax=ax)

            ax.tick_params(axis='y', which='major', length=5, width=1)
            ax.tick_params(axis='x', which='major', length=5, width=1)
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(reversed(handles), reversed(labels), loc='lower left',
                      bbox_to_anchor=(1, 0), facecolor='inherit', frameon=True)
            if mconfig.parser("plot_title_as_region"):
                ax.set_title(zone_input)

            outputs[zone_input] = {'fig': fig1, 'data_table': Data_Table_Out}
        return outputs

    def total_cap_diff(self, **_):
        """Creates a stacked barplot of total installed capacity relative to a base scenario.

        Barplots show the change in total installed capacity relative to a base scenario.
        The default is to comapre against the first scenario provided in the inputs list.
        Each sceanrio is plotted as a separate bar.

        Returns:
            dict: Dictionary containing the created plot and its data table.
        """
        outputs = {}
        # List of properties needed by the plot, properties are a set of tuples and contain 3 parts:
        # required True/False, property name and scenarios required, scenarios must be a list.
        properties = [(True, "generator_Installed_Capacity", self.Scenarios)]

        # Runs get_formatted_data within PlotDataHelper to populate PlotDataHelper dictionary  
        # with all required properties, returns a 1 if required data is missing
        check_input_data = self.get_formatted_data(properties)

        # Checks if all data required by plot is available, if 1 in list required data is missing
        if 1 in check_input_data:
            outputs = MissingInputData()
            return outputs

        for zone_input in self.Zones:
            Total_Installed_Capacity_Out = pd.DataFrame()
            self.logger.info(f"{self.AGG_BY} = {zone_input}")

            for scenario in self.Scenarios:

                self.logger.info(f"Scenario = {scenario}")

                Total_Installed_Capacity = self["generator_Installed_Capacity"].get(scenario)
                zones_with_cap = Total_Installed_Capacity.index.get_level_values(self.AGG_BY).unique()
                if scenario == 'ADS':
                    zone_input_adj = zone_input.split('_WI')[0]
                    Total_Installed_Capacity.index = pd.MultiIndex.from_frame(Total_Installed_Capacity
                                                                              .index
                                                                              .to_frame()
                                                                              .fillna('All'))  # Fix NaN values from formatter
                    zones_with_cap = Total_Installed_Capacity.index.get_level_values(self.AGG_BY).unique()
                else:
                    zone_input_adj = zone_input
                if zone_input_adj in zones_with_cap:
                    Total_Installed_Capacity = Total_Installed_Capacity.xs(zone_input_adj, level=self.AGG_BY)
                else:
                    self.logger.warning(f"No installed capacity in {zone_input}")
                    outputs[zone_input] = MissingZoneData()
                    continue

                # print(Total_Installed_Capacity.index.get_level_values('tech').unique())
                fn = os.path.join(self.Marmot_Solutions_folder,
                                  'Figures_Output',
                                  f'{self.AGG_BY}_total_installed_capacity',
                                  'Individual_Gen_Cap_{scenario}.csv')

                Total_Installed_Capacity.reset_index().to_csv(fn)

                Total_Installed_Capacity = self.df_process_gen_inputs(Total_Installed_Capacity)
                Total_Installed_Capacity.reset_index(drop=True, inplace=True)
                Total_Installed_Capacity.rename(index={0: scenario}, inplace=True)
                Total_Installed_Capacity_Out = pd.concat([Total_Installed_Capacity_Out, Total_Installed_Capacity],
                                                         axis=0, sort=False).fillna(0)

            try:
                # Change to a diff on first scenario
                Total_Installed_Capacity_Out = Total_Installed_Capacity_Out-Total_Installed_Capacity_Out.xs(self.Scenarios[0])  
            except KeyError:
                out = MissingZoneData()
                outputs[zone_input] = out
                continue
            Total_Installed_Capacity_Out.drop(self.Scenarios[0], inplace=True)  # Drop base entry

            Total_Installed_Capacity_Out = Total_Installed_Capacity_Out.loc[:, (Total_Installed_Capacity_Out != 0).any(axis=0)]

            # If Total_Installed_Capacity_Out df is empty returns a empty dataframe and does not plot
            if Total_Installed_Capacity_Out.empty:
                self.logger.warning(f"No installed capacity in {zone_input}")
                out = MissingZoneData()
                outputs[zone_input] = out
                continue

            unitconversion = PlotDataHelper.capacity_energy_unitconversion(max(Total_Installed_Capacity_Out.sum()))
            Total_Installed_Capacity_Out = Total_Installed_Capacity_Out/unitconversion['divisor']

            Data_Table_Out = Total_Installed_Capacity_Out
            Data_Table_Out = Data_Table_Out.add_suffix(f" ({unitconversion['units']})")

            Total_Installed_Capacity_Out.index = Total_Installed_Capacity_Out.index.str.replace('_', ' ')

            fig2, ax = plt.subplots(figsize=(self.x, self.y))

            Total_Installed_Capacity_Out.plot.bar(stacked=True, ax=ax,
                                                  color=[self.PLEXOS_color_dict.get(x, '#333333') 
                                                         for x in Total_Installed_Capacity_Out.columns],
                                                  edgecolor='black', linewidth='0.1')

            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.set_ylabel((f"Capacity Change ({unitconversion['units']}) \n "
                           f"relative to {self.Scenarios[0]}"), color='black', rotation='vertical')
            ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(
                                         lambda x, p: format(x, f',.{self.y_axes_decimalpt}f')))
            
            tick_labels = Total_Installed_Capacity_Out.index
            PlotDataHelper.set_barplot_xticklabels(tick_labels, ax=ax)

            ax.tick_params(axis='y', which='major', length=5, width=1)
            ax.tick_params(axis='x', which='major', length=5, width=1)

            handles, labels = ax.get_legend_handles_labels()
            ax.legend(reversed(handles), reversed(labels), loc='lower left',
                      bbox_to_anchor=(1, 0), facecolor='inherit', frameon=True)
            if mconfig.parser("plot_title_as_region"):
                ax.set_title(zone_input)
                
            outputs[zone_input] = {'fig': fig2, 'data_table': Data_Table_Out}
        return outputs

    def total_cap_and_gen_facet(self, **_):
        """Creates a facet plot comparing total generation and installed capacity.

        Creates a plot with 2 facet plots, total installed capacity on the left 
        and total generation on the right. 
        Each facet contains stacked bar plots, each scenario is plotted as a 
        separate bar.

        Returns:
            dict: Dictionary containing the created plot and its data table.
        """
        # generation figure
        self.logger.info("Generation data")
        # gen_obj = gen.mplot(self.argument_dict)
        gen_obj = gen.MPlot(self.argument_dict)
        gen_outputs = gen_obj.total_gen()

        self.logger.info("Installed capacity data")
        cap_outputs = self.total_cap()

        outputs = {}
        for zone_input in self.Zones:

            fig, axs = plt.subplots(1, 2, figsize=(10, 4))

            plt.subplots_adjust(wspace=0.35, hspace=0.2)
            axs = axs.ravel()

            # left panel: installed capacity
            try:
                Total_Installed_Capacity_Out = cap_outputs[zone_input]["data_table"]
            except TypeError:
                outputs[zone_input] = MissingZoneData()
                continue

            Total_Installed_Capacity_Out.index = Total_Installed_Capacity_Out.index.str.replace('_', ' ')

            # Check units of data
            capacity_units = [re.search('GW|MW|TW|kW', unit) for unit in Total_Installed_Capacity_Out.columns]
            capacity_units = [unit for unit in capacity_units if unit is not None][0].group()

            # Remove any suffixes from column names
            Total_Installed_Capacity_Out.columns = [re.sub('[\s (]|GW|TW|MW|kW|\)', '', i) 
                                                    for i in Total_Installed_Capacity_Out.columns]


            Total_Installed_Capacity_Out.plot.bar(stacked=True, ax=axs[0],
                                                  color=[self.PLEXOS_color_dict.get(x, '#333333') 
                                                         for x in Total_Installed_Capacity_Out.columns],
                                                  edgecolor='black', linewidth='0.1')

            axs[0].spines['right'].set_visible(False)
            axs[0].spines['top'].set_visible(False)
            axs[0].set_ylabel(f"Total Installed Capacity ({capacity_units})", 
                              color='black', rotation='vertical')
            axs[0].yaxis.set_major_formatter(mpl.ticker.FuncFormatter(
                                             lambda x, p: format(x, f',.{self.y_axes_decimalpt}f')))
            
            if len(self.custom_xticklabels) > 1:
                tick_labels = self.custom_xticklabels
            else:
                tick_labels = Total_Installed_Capacity_Out.index
            PlotDataHelper.set_barplot_xticklabels(tick_labels, ax=axs[0])
            
            axs[0].tick_params(axis='y', which='major', length=5, width=1)
            axs[0].tick_params(axis='x', which='major', length=5, width=1)
            axs[0].get_legend().remove()

            # right panel: annual generation
            Total_Gen_Results = gen_outputs[zone_input]["data_table"]

            # Check units of data
            energy_units = [re.search('GWh|MWh|TWh|kWh', unit) for unit in Total_Gen_Results.columns]
            energy_units = [unit for unit in energy_units if unit is not None][0].group()

            def check_column_substring(df, substring):
                '''
                Checks if df column contains substring and returns actual column name,
                this is required as columns contain suffixes

                '''
                return [column for column in list(df.columns) if substring in column][0]

            Total_Load_Out = Total_Gen_Results.loc[:, check_column_substring(Total_Gen_Results, 
                                                                             "Total Load (Demand + \n Storage Charging)")]
            Total_Demand_Out = Total_Gen_Results.loc[:, check_column_substring(Total_Gen_Results, 
                                                                               "Total Demand")]
            Unserved_Energy_Out = Total_Gen_Results.loc[:, check_column_substring(Total_Gen_Results, 
                                                                                  "Unserved Energy")]
            Total_Generation_Stack_Out = Total_Gen_Results.drop([check_column_substring(Total_Gen_Results,
                                                                                        "Total Load (Demand + \n Storage Charging)"),
                                                                 check_column_substring(Total_Gen_Results, 
                                                                                        "Total Demand"),
                                                                 check_column_substring(Total_Gen_Results, 
                                                                                        "Unserved Energy")], axis=1)

            Pump_Load_Out = Total_Load_Out - Total_Demand_Out

            Total_Generation_Stack_Out.index = Total_Generation_Stack_Out.index.str.replace('_', ' ')

            # Remove any suffixes from column names
            Total_Generation_Stack_Out.columns = [re.sub('[\s (]|GWh|TWh|MWh|kWh|\)', '', i) 
                                                  for i in Total_Generation_Stack_Out.columns]

            Total_Generation_Stack_Out.plot.bar(stacked=True, ax=axs[1],
                                                color=[self.PLEXOS_color_dict.get(x, '#333333') 
                                                       for x in Total_Generation_Stack_Out.columns],
                                                edgecolor='black', linewidth='0.1')

            axs[1].spines['right'].set_visible(False)
            axs[1].spines['top'].set_visible(False)
            axs[1].set_ylabel(f"Total Generation ({energy_units})", 
                              color='black', rotation='vertical')
            axs[1].yaxis.set_major_formatter(mpl.ticker.FuncFormatter(
                                             lambda x, p: format(x, f',.{self.y_axes_decimalpt}f')))
            
            if len(self.custom_xticklabels) > 1:
                tick_labels = self.custom_xticklabels
            else:
                tick_labels = Total_Generation_Stack_Out.index
            PlotDataHelper.set_barplot_xticklabels(tick_labels, ax=axs[1])
            
            axs[1].tick_params(axis='y', which='major', length=5, width=1)
            axs[1].tick_params(axis='x', which='major', length=5, width=1)

            data_tables = []
            for n, scenario in enumerate(self.Scenarios):

                x = [axs[1].patches[n].get_x(), axs[1].patches[n].get_x() + 
                     axs[1].patches[n].get_width()]
                height1 = [float(Total_Load_Out[scenario])]*2
                lp1 = plt.plot(x, height1, c='black', linewidth=1.5)
                height2 = [float(Total_Demand_Out[scenario])]*2
                lp2 = plt.plot(x, height2, 'r--', c='black', linewidth=1.5)
                if Unserved_Energy_Out[scenario].sum() > 0:
                    height3 = [float(Unserved_Energy_Out[scenario])]*2
                    plt.plot(x, height3, c='#DD0200', linewidth=1.5)
                    axs[1].fill_between(x, height3, height1,
                                        facecolor='#DD0200',
                                        alpha=0.5)

                data_tables = pd.DataFrame() #TODO pass output data back to plot main 

            # get names of generator to create custom legend
            l1 = Total_Installed_Capacity_Out.columns.tolist()
            l2 = Total_Generation_Stack_Out.columns.tolist()
            l1.extend(l2)

            labels = np.unique(np.array(l1)).tolist()
            labels.sort(key=lambda i: self.ordered_gen.index(i))
            # create custom gen_tech legend
            handles = []
            for tech in labels:
                gen_tech_legend = Patch(facecolor=self.PLEXOS_color_dict[tech],
                                        alpha=1.0)
                handles.append(gen_tech_legend)

            if Pump_Load_Out.values.sum() > 0:
                handles.append(lp2[0])
                handles.append(lp1[0])
                labels += ['Demand', 'Demand + \n Storage Charging']

            else:
                handles.append(lp1[0])
                labels += ['Demand']

            if Unserved_Energy_Out.values.sum() > 0:
                handles.append(custom_legend_elements)
                labels += ['Unserved Energy']

            axs[1].legend(reversed(handles), reversed(labels),
                          loc='lower left', bbox_to_anchor=(1.05, 0),
                          facecolor='inherit', frameon=True)

            # add labels to panels
            axs[0].set_title("A.", fontdict={"weight": "bold", "size": 11}, loc='left', pad=4)
            axs[1].set_title("B.", fontdict={"weight": "bold", "size": 11}, loc='left', pad=4)
            
            fig.add_subplot(111, frameon=False)
            plt.tick_params(labelcolor='none', top=False, bottom=False, 
                            left=False, right=False)
            if mconfig.parser('plot_title_as_region'):
                plt.title(zone_input)

            # output figure
            outputs[zone_input] = {'fig': fig, 'data_table': data_tables}

        return outputs
