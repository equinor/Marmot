# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 10:34:48 2019

This code creates generation stack plots and is called from Marmot_plot_main.py

@author: dlevie
"""

import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates
import os
from matplotlib.patches import Patch


#===============================================================================

def df_process_gen_inputs(df, self):
    df = df.reset_index()
    df = df[df['tech'].isin(self.thermal_gen_cat)]  #Optional, select which technologies to show.
    df = df.groupby(["timestamp", "tech"], as_index=False).sum()
    df.tech = df.tech.astype("category")
    df.tech.cat.set_categories(self.ordered_gen, inplace=True)
    df = df.sort_values(["tech"])
    df = df.pivot(index='timestamp', columns='tech', values=0)
    return df


custom_legend_elements = [Patch(facecolor='#DD0200',
                            alpha=0.5, edgecolor='#DD0200',
                         label='Unserved Energy')]

class mplot(object):

    def __init__(self,argument_list):

        self.prop = argument_list[0]
        self.start = argument_list[1]
        self.end = argument_list[2]
        self.timezone = argument_list[3]
        self.start_date = argument_list[4]
        self.end_date = argument_list[5]
        self.hdf_out_folder = argument_list[6]
        self.zone_input =argument_list[7]
        self.AGG_BY = argument_list[8]
        self.ordered_gen = argument_list[9]
        self.PLEXOS_color_dict = argument_list[10]
        self.Multi_Scenario = argument_list[11]
        self.Scenario_Diff = argument_list[12]
        self.PLEXOS_Scenarios = argument_list[13]
        self.ylabels = argument_list[14]
        self.xlabels = argument_list[15]
        self.gen_names_dict = argument_list[18]
        self.vre_gen_cat = argument_list[21]
        self.thermal_gen_cat = argument_list[23]


    def thermal_cap_reserves(self):

        print("Zone = "+ self.zone_input)

        xdimension=len(self.xlabels)
        if xdimension == 0:
            xdimension = 1
        ydimension=len(self.ylabels)
        if ydimension == 0:
            ydimension = 1

        fig1, axs = plt.subplots(ydimension,xdimension, figsize=((8*xdimension),(4*ydimension)), sharey=True)
        plt.subplots_adjust(wspace=0.05, hspace=0.2)
        if len(self.Multi_Scenario) > 1:
            axs = axs.ravel()
        i=0

        for scenario in self.Multi_Scenario:

            print("Scenario = " + scenario)

            avail_cap = pd.read_hdf(os.path.join(self.PLEXOS_Scenarios, scenario, "Processed_HDF5_folder", scenario + "_formatted.h5"), "generator_Available_Capacity")
            Gen = pd.read_hdf(os.path.join(self.PLEXOS_Scenarios, scenario, "Processed_HDF5_folder", scenario + "_formatted.h5"), "generator_Generation")

            avail_cap = avail_cap.xs(self.zone_input,level = self.AGG_BY)
            Gen = Gen.xs(self.zone_input,level = self.AGG_BY)
            avail_cap = df_process_gen_inputs(avail_cap,self)
            Gen = df_process_gen_inputs(Gen,self)
            Gen = Gen.loc[:, (Gen != 0).any(axis=0)]

            thermal_reserve = avail_cap - Gen

            if '2008' not in self.PLEXOS_Scenarios and '2012' not in self.PLEXOS_Scenarios and thermal_reserve.index[0] > dt.datetime(2024,2,28,0,0):
                thermal_reserve.index = thermal_reserve.index.shift(1,freq = 'D') #TO DEAL WITH LEAP DAYS, SPECIFIC TO MARTY'S PROJECT, REMOVE AFTER.

            Data_Table_Out = thermal_reserve

            locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
            formatter = mdates.ConciseDateFormatter(locator)
            formatter.formats[2] = '%d\n %b'
            formatter.zero_formats[1] = '%b\n %Y'
            formatter.zero_formats[2] = '%d\n %b'
            formatter.zero_formats[3] = '%H:%M\n %d-%b'
            formatter.offset_formats[3] = '%b %Y'
            formatter.show_offset = False

            if len(self.Multi_Scenario) > 1:
                sp = axs[i].stackplot(thermal_reserve.index.values, thermal_reserve.values.T, labels = thermal_reserve.columns, linewidth=0,
                             colors = [self.PLEXOS_color_dict.get(x, '#333333') for x in thermal_reserve.T.index])

                axs[i].spines['right'].set_visible(False)
                axs[i].spines['top'].set_visible(False)
                axs[i].tick_params(axis='y', which='major', length=5, width=1)
                axs[i].tick_params(axis='x', which='major', length=5, width=1)
                axs[i].yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
                axs[i].margins(x=0.01)
                axs[i].xaxis.set_major_locator(locator)
                axs[i].xaxis.set_major_formatter(formatter)
                handles, labels = axs[i].get_legend_handles_labels()
                #Legend 1
                leg1 = axs[i].legend(reversed(handles), reversed(labels), loc='lower left',bbox_to_anchor=(1,0),facecolor='inherit', frameon=True)
                # Manually add the first legend back
                axs[i].add_artist(leg1)

            else:
                sp = axs.stackplot(thermal_reserve.index.values, thermal_reserve.values.T, labels = thermal_reserve.columns, linewidth=0,
                             colors = [self.PLEXOS_color_dict.get(x, '#333333') for x in thermal_reserve.T.index])

                axs.spines['right'].set_visible(False)
                axs.spines['top'].set_visible(False)
                axs.tick_params(axis='y', which='major', length=5, width=1)
                axs.tick_params(axis='x', which='major', length=5, width=1)
                axs.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
                axs.margins(x=0.01)
                axs.xaxis.set_major_locator(locator)
                axs.xaxis.set_major_formatter(formatter)
                handles, labels = axs.get_legend_handles_labels()
                #Legend 1
                leg1 = axs.legend(reversed(handles), reversed(labels), loc='lower left',bbox_to_anchor=(1,0),facecolor='inherit', frameon=True)
                # Manually add the first legend back
                axs.add_artist(leg1)

            i=i+1

        all_axes = fig1.get_axes()

        self.xlabels = pd.Series(self.xlabels).str.replace('_',' ').str.wrap(10, break_long_words=False)

        j=0
        k=0
        for ax in all_axes:
            if ax.is_last_row():
                ax.set_xlabel(xlabel=(self.xlabels[j]),  color='black')
                j=j+1
            if ax.is_first_col():
                ax.set_ylabel(ylabel=(self.ylabels[k]),  color='black', rotation='vertical')
                k=k+1

        fig1.add_subplot(111, frameon=False)
        plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
        plt.ylabel('Thermal capacity reserve (MW)',  color='black', rotation='vertical', labelpad=60)

        #fig1.savefig('/home/mschwarz/PLEXOS results analysis/test/SPP_thermal_cap_reserves_test', dpi=600, bbox_inches='tight') #Test

        return {'fig': fig1, 'data_table': Data_Table_Out}
