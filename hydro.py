# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 10:34:48 2019

This code creates hydro analysis and is called from Marmot_plot_main.py

@author: adyreson
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
    df = df.reset_index(['timestamp','tech'])
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
        self.Zones =argument_list[7]
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
        self.figure_folder = argument_list[25]
    

    def hydro_net_load(self):
        outputs = {}
        for zone_input in self.Zones:
        #Location to save to
            hydro_figures = os.path.join(self.figure_folder, self.AGG_BY + '_Hydro')
    
            Stacked_Gen_read = pd.read_hdf(self.hdf_out_folder + "/" + self.Multi_Scenario[0]+"_formatted.h5", 'generator_Generation')
            
            print("Zone = "+ zone_input)
           # try:   #The rest of the function won't work if this particular zone can't be found in the solution file (e.g. if it doesn't include Mexico)
            Stacked_Gen = Stacked_Gen_read.xs(zone_input,level=self.AGG_BY)  
            del Stacked_Gen_read
            Stacked_Gen = df_process_gen_inputs(Stacked_Gen, self)
               
            # Calculates Net Load by removing variable gen
            # Adjust list of values to drop depending on if it exhists in Stacked_Gen df
            self.vre_gen_cat = [name for name in self.vre_gen_cat if name in Stacked_Gen.columns]
            Net_Load = Stacked_Gen.drop(labels = self.vre_gen_cat, axis=1)
            Net_Load = Net_Load.sum(axis=1)
            
            # Removes columns that only contain 0
            Stacked_Gen = Stacked_Gen.loc[:, (Stacked_Gen != 0).any(axis=0)]
            try:
                Hydro_Gen = Stacked_Gen['Hydro']
            except KeyError:
                print("No hydro in "+ zone_input+".")
                Hydro_Gen=pd.DataFrame()
                continue
                
            del Stacked_Gen
            
            first_date=Net_Load.index[0]
            for wk in range(1,53): #assumes weekly, could be something else if user changes self.end Marmot_plot_select
                        
                period_start=first_date+dt.timedelta(days=(wk-1)*7) 
                period_end=period_start+dt.timedelta(days=self.end)
                print(str(period_start)+" and next "+str(self.end)+" days.")
                Hydro_Period = Hydro_Gen[period_start:period_end]
                Net_Load_Period = Net_Load[period_start:period_end]
                #print(Net_Load_Period)              
                    
                # Data table of values to return to main program
                Data_Table_Out = pd.concat([Net_Load_Period, Hydro_Period], axis=1, sort=False)
                
                fig1, ax = plt.subplots(figsize=(9,6))
    
                ax.plot(Hydro_Period, linewidth=2, 
                       color=self.PLEXOS_color_dict.get('Hydro','#333333'),label='Hydro')            
    
        
                ax.plot(Net_Load_Period, color='black',label='Load')
                
                           
                
                ax.set_ylabel('Generation (MW)',  color='black', rotation='vertical')
                ax.set_xlabel('Date ' + '(' + str(self.timezone) + ')',  color='black', rotation='horizontal')
                ax.spines['right'].set_visible(False)
                ax.spines['top'].set_visible(False)
                ax.tick_params(axis='y', which='major', length=5, width=1)
                ax.tick_params(axis='x', which='major', length=5, width=1)
                ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
                ax.margins(x=0.01)
                
                locator = mdates.AutoDateLocator(minticks=6, maxticks=12)
                formatter = mdates.ConciseDateFormatter(locator)
                formatter.formats[2] = '%d\n %b'
                formatter.zero_formats[1] = '%b\n %Y'
                formatter.zero_formats[2] = '%d\n %b'
                formatter.zero_formats[3] = '%H:%M\n %d-%b'
                formatter.offset_formats[3] = '%b %Y'
                formatter.show_offset = False
                ax.xaxis.set_major_locator(locator)
                ax.xaxis.set_major_formatter(formatter)
                 
                        
               
                handles, labels = ax.get_legend_handles_labels()
                
             
                #Legend 1
                leg1 = ax.legend(reversed(handles), reversed(labels), loc='lower left',bbox_to_anchor=(1,0), 
                              facecolor='inherit', frameon=True)  
               
                
                
                # Manually add the first legend back
                ax.add_artist(leg1)
                
        
                fig1.savefig(os.path.join(hydro_figures, zone_input + "_" + "Hydro_And_Net_Load" + "_" + self.Multi_Scenario[0]+"_period_"+str(wk)), dpi=600, bbox_inches='tight')
                Data_Table_Out.to_csv(os.path.join(hydro_figures, zone_input + "_" + "Hydro_Versus_Net_Load" + "_" + self.Multi_Scenario[0]+"_period_"+str(wk)+ ".csv"))
                del fig1
                del Data_Table_Out
                mpl.pyplot.close('all')
            #end weekly loop
            
            
            #Scatter plot 
            fig2, ax2 = plt.subplots(figsize=(9,6))
    
            ax2.scatter(Net_Load,Hydro_Gen,color='black',s=5)        
    
            ax2.set_ylabel('In-Region Hydro Generation (MW)',  color='black', rotation='vertical')
            ax2.set_xlabel('In-Region Net Load (MW)',  color='black', rotation='horizontal')
            ax2.spines['right'].set_visible(False)
            ax2.spines['top'].set_visible(False)
            ax2.tick_params(axis='y', which='major', length=5, width=1)
            ax2.tick_params(axis='x', which='major', length=5, width=1)
            ax2.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
            ax2.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
            ax2.margins(x=0.01)
            
            handles, labels = ax2.get_legend_handles_labels()
                
            leg1 = ax2.legend(reversed(handles), reversed(labels), loc='lower left',bbox_to_anchor=(1,0), 
                              facecolor='inherit', frameon=True)  
         
              
            ax2.add_artist(leg1)
            
            fig2.savefig(os.path.join(hydro_figures, zone_input + "_" + "Hydro_Versus_Net_Load" + "_" + self.Multi_Scenario[0]), dpi=600, bbox_inches='tight')
            outputs[zone_input] = pd.DataFrame()
        return outputs
    
    def hydro_continent_net_load(self):
        outputs = {}
        for zone_input in self.Zones:    
            #Location to save to
            hydro_figures = os.path.join(self.figure_folder, self.AGG_BY + '_Hydro')
    
            Stacked_Gen_read = pd.read_hdf(self.hdf_out_folder + "/" + self.Multi_Scenario[0]+"_formatted.h5", 'generator_Generation')
            
            print("Zone = "+ zone_input)
            print("Winter is defined as date range:")
            print(str(self.start_date) + '  to  ' + str(self.end_date))       
            Net_Load = df_process_gen_inputs(Stacked_Gen_read, self)
        
            # Calculates Net Load by removing variable gen
            # Adjust list of values to drop depending on if it exhists in Stacked_Gen df
            self.vre_gen_cat = [name for name in self.vre_gen_cat if name in Net_Load.columns]
            Net_Load = Net_Load.drop(labels = self.vre_gen_cat, axis=1) 
            Net_Load = Net_Load.sum(axis=1) # Continent net load
            
            Stacked_Gen = Stacked_Gen_read.xs(zone_input,level=self.AGG_BY)  
            del Stacked_Gen_read
            Stacked_Gen= df_process_gen_inputs(Stacked_Gen, self)
            Stacked_Gen = Stacked_Gen.loc[:, (Stacked_Gen != 0).any(axis=0)] #Removes columns only containing 0
    
            try:
                Hydro_Gen = Stacked_Gen['Hydro']
            except KeyError:
                print("No hydro in "+ zone_input+".")
                Hydro_Gen=pd.DataFrame()
                continue
                
            del Stacked_Gen
            
                   
            
            #Scatter plot by season
            fig2, ax2 = plt.subplots(figsize=(9,6))
    
            ax2.scatter(Net_Load[self.end_date:self.start_date],
                        Hydro_Gen[self.end_date:self.start_date],color='black',s=5,label='Non-winter')        
            ax2.scatter(Net_Load[self.start_date:],Hydro_Gen[self.start_date:],color='blue',s=5,label='Winter',alpha=0.5)
            ax2.scatter(Net_Load[:self.end_date],Hydro_Gen[:self.end_date],color='blue',s=5,alpha=0.5)
    
    
            ax2.set_ylabel('In Region Hydro Generation (MW)',  color='black', rotation='vertical')
            ax2.set_xlabel('Continent Net Load (MW)',  color='black', rotation='horizontal')
            ax2.spines['right'].set_visible(False)
            ax2.spines['top'].set_visible(False)
            ax2.tick_params(axis='y', which='major', length=5, width=1)
            ax2.tick_params(axis='x', which='major', length=5, width=1)
            ax2.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
            ax2.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
            ax2.margins(x=0.01)
            
            handles, labels = ax2.get_legend_handles_labels()
                
            leg1 = ax2.legend(reversed(handles), reversed(labels), loc='lower left',bbox_to_anchor=(1,0), 
                              facecolor='inherit', frameon=True)  
         
              
            ax2.add_artist(leg1)
            
            fig2.savefig(os.path.join(hydro_figures, zone_input + "_" + "Hydro_Versus_Continent_Net_Load" + "_" + self.Multi_Scenario[0]), dpi=600, bbox_inches='tight')
            outputs[zone_input] = pd.DataFrame()
        return outputs