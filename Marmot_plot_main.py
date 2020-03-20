# -*- coding: utf-8 -*-
"""
Created on Thu Dec  5 14:16:30 2019

@author: dlevie
"""
#%%
import pandas as pd
import os
import matplotlib as mpl
import generation_stack
import total_generation 
import total_installed_capacity
import capacity_factor
import curtailment
import production_cost
import unserved_energy
import reserves
import generation_unstack
import transmission
import ramping

#===============================================================================
# Graphing Defaults
#===============================================================================

mpl.rc('xtick', labelsize=11) 
mpl.rc('ytick', labelsize=12) 
mpl.rc('axes', labelsize=16)
mpl.rc('legend', fontsize=11)
mpl.rc('font', family='serif')


#===============================================================================
""" User Defined Names, Directories and Settings """
#===============================================================================

# Directory of cloned Marmot repo and loaction of this file
Marmot_DIR = "/Users/mschwarz/EXTREME EVENTS/PLEXOS results analysis/Marmot"
os.chdir(Marmot_DIR)

Marmot_plot_select = pd.read_csv("Marmot_plot_select.csv")

Scenario_name = 'Cold Wave 2011' # 'BAU' # "BAU_No_VG_Reserves"

Solutions_folder = '../TB_2024/StageA_DA'

Multi_Scenario = ['Cold Wave 2011'] # ['BAU']
#Multi_Scenario = ['Base','NoCSP']

# For plots using the differnec of the values between two scenarios. 
# Max two entries, the second scenario is subtracted from the first. 
Scenario_Diff = []
#Scenario_Diff = ['Base','NoCSP'] # ["Gas_Outage_+_Icing", "Base_Case"]

Mapping_folder = 'mapping_folder'

Region_Mapping = pd.read_csv(os.path.join(Mapping_folder, 'Region_mapping.csv'))
Reserve_Regions = pd.read_csv(os.path.join(Mapping_folder, 'reserve_region_type.csv'))
gen_names = pd.read_csv(os.path.join(Mapping_folder, 'gen_names.csv'))


AGG_BY = 'Interconnection' # "Usual"

# Facet Grid Labels (Based on Scenarios)
ylabels = [] # ["BAU", "BAU2"]
xlabels = [] # ["No VG Reserves", "VG Reserves", "Copperplate"]

#===============================================================================
# Input and Output Directories 
#===============================================================================


PLEXOS_Scenarios = os.path.join(Solutions_folder, 'PLEXOS_Scenarios')
# PLEXOS_Scenarios = '/Volumes/PLEXOS/Projects/Drivers_of_Curtailment/PLEXOS_Scenarios'

figure_folder = os.path.join(PLEXOS_Scenarios, Scenario_name, 'Figures_Output')
try:
    os.makedirs(figure_folder)
except FileExistsError:
    # directory already exists
    pass


hdf_out_folder = os.path.join(PLEXOS_Scenarios, Scenario_name,'Processed_HDF5_folder')
try:
    os.makedirs(hdf_out_folder)
except FileExistsError:
    # directory already exists
    pass

gen_stack_figures = os.path.join(figure_folder, AGG_BY + '_Gen_Stack')
try:
    os.makedirs(gen_stack_figures)
except FileExistsError:
    # directory already exists
    pass    
tot_gen_stack_figures = os.path.join(figure_folder, AGG_BY + '_Total_Gen_Stack')
try:
    os.makedirs(tot_gen_stack_figures)
except FileExistsError:
    # directory already exists
    pass    
installed_cap_figures = os.path.join(figure_folder, AGG_BY + '_Total_Installed_Capacity')
try:
    os.makedirs(installed_cap_figures)
except FileExistsError:
    # directory already exists
    pass                           
capacity_factor_figures = os.path.join(figure_folder, AGG_BY + '_Capacity_Factor')
try:
    os.makedirs(capacity_factor_figures)
except FileExistsError:
    # directory already exists
    pass          
system_cost_figures = os.path.join(figure_folder, AGG_BY + '_Total_System_Cost')
try:
    os.makedirs(system_cost_figures)
except FileExistsError:
    # directory already exists
    pass                
reserve_timeseries_figures = os.path.join(figure_folder, AGG_BY + '_Reserve_Timeseries')
try:
    os.makedirs(reserve_timeseries_figures)
except FileExistsError:
    # directory already exists
    pass   
reserve_total_figures = os.path.join(figure_folder, AGG_BY + '_Reserve_Total')
try:
    os.makedirs(reserve_total_figures)
except FileExistsError:
    # directory already exists
    pass          
transmission_figures = os.path.join(figure_folder, AGG_BY + '_Transmission')
try:
    os.makedirs(transmission_figures)
except FileExistsError:
    pass                
ramping_figures = os.path.join(figure_folder, AGG_BY + '_Ramping')
try:
    os.makedirs(ramping_figures)
except FileExistsError:
    pass           

#===============================================================================
# Standard Generation Order
#===============================================================================

ordered_gen = ['Nuclear',
               'Coal',
               'Gas-CC',
               'Gas-CC CCS',
               'Gas-CT',
               'Gas',
               'Gas-Steam',
               'DualFuel',
               'Oil-Gas-Steam',
               'Oil',
               'Hydro',
               'Ocean', 
               'Geothermal',
               'Biomass',
               'Biopower',
               'Other',
               'Wind',
               'Solar',
               'CSP',
               'PV',
               'PV-Battery',
               'Battery',
               'PHS',
               'Storage',
               'Net Imports',
               'Curtailment']

pv_gen_cat = ['Solar',
              'PV']

re_gen_cat = ['Wind',
              'PV']

vre_gen_cat = ['Hydro',
               'Ocean',
               'Geothermal',
               'Biomass',
               'Biopwoer',
               'Wind',
               'Solar',
               'CSP',
               'PV']

if set(gen_names["New"].unique()).issubset(ordered_gen) == False:
                    print("\n WARNING!! The new categories from the gen_names csv do not exist in ordered_gen \n")
                    print(set(gen_names["New"].unique()) - (set(ordered_gen)))

#===============================================================================
# Colours and styles
#===============================================================================

#ORIGINAL MARMOT COLORS             
# PLEXOS_color_dict = {'Nuclear':'#B22222',
#                     'Coal':'#333333',
#                     'Gas-CC':'#6E8B3D',
#                     'Gas-CC CCS':'#396AB1',
#                     'Gas-CT':'#FFB6C1',
#                     'DualFuel':'#000080',
#                     'Oil-Gas-Steam':'#cd5c5c',
#                     'Hydro':'#ADD8E6',
#                     'Ocean':'#000080',
#                     'Geothermal':'#eedc82',
#                     'Biopower':'#008B00',
#                     'Wind':'#4F94CD',
#                     'CSP':'#EE7600',
#                     'PV':'#FFC125',
#                     'PV-Battery':'#CD950C',
#                     'Storage':'#dcdcdc',
#                     'Other': '#9370DB',
#                     'Net Imports':'#efbbff',
#                     'Curtailment': '#FF0000'}  
                    

# color_list = ['#396AB1', '#CC2529','#3E9651','#ff7f00','#6B4C9A','#922428','#cab2d6', '#6a3d9a', '#fb9a99', '#b15928']

#STANDARD SEAC COLORS (AS OF MARCH 9, 2020)             
PLEXOS_color_dict = {'Nuclear':'#820000',
                    'Coal':'#222222',
                    'Gas-CC':'#52216B',
                    'Gas-CC CCS':'#5E1688',
                    'Gas-CT':'#C2A1DB',
                    'DualFuel':'#000080',
                    'Oil-Gas-Steam':'#3D3376',
                    'Hydro':'#187F94',
                    'Ocean':'#000080',
                    'Geothermal':'#A96235',
                    'Biopower':'#5B9844',
                    'Wind':'#00B6EF',
                    'CSP':'#FC761A',
                    'PV':'#FFC903',
                    'PV-Battery':'#D1C202',
                    'Storage':'#FF4A88',
                    'Other': '#FF7FBB',
                    'Net Imports':'#193A71',
                    'Curtailment': '#5B6272'}  
                    

color_list = ['#396AB1', '#CC2529','#3E9651','#ff7f00','#6B4C9A','#922428','#cab2d6', '#6a3d9a', '#fb9a99', '#b15928']


marker_style = ["^", "*", "o", "D", "x", "<", "P", "H", "8", "+"]

#===============================================================================
# Main          
#===============================================================================                   
 
gen_names_dict=gen_names[['Original','New']].set_index("Original").to_dict()["New"]

if AGG_BY=="zone":
    Zones = pd.read_pickle('zones.pkl')
    Zones = Zones['name'].unique()
elif Region_Mapping.empty==True:
    Zones = pd.read_pickle('regions.pkl') 
    Zones = Zones['name'].unique()
else:     
    Zones = Region_Mapping[AGG_BY].unique()


Reserve_Regions = Reserve_Regions["Reserve_Region"].unique()

# Filter for chosen figures to plot
Marmot_plot_select = Marmot_plot_select.loc[Marmot_plot_select["Plot Graph"] == True]

#%%
# Main loop to process each figure and pass data to functions
for index, row in Marmot_plot_select.iterrows():
    
    print("                 ")
    print("                 ")
    print("                 ")
    print("Plot =  " + row["Figure Output Name"])
    
# Checks if figure type is a reserve figure. This is required as reserve regions dont always match generator regions/zones    
    if "Reserve" in row["Figure Type"]:
        
        for region in Reserve_Regions:
            
            argument_list = [row.iloc[3], row.iloc[4], row.iloc[5], row.iloc[6], row.iloc[7], row.iloc[8],
                                  hdf_out_folder, Zones, AGG_BY, ordered_gen, PLEXOS_color_dict, Multi_Scenario,
                                  Scenario_Diff, PLEXOS_Scenarios, ylabels, xlabels, color_list, marker_style, gen_names_dict, pv_gen_cat, 
                                  re_gen_cat, vre_gen_cat, region]
            
            if row["Figure Type"] == "Reserve Timeseries":
                fig = reserves.mplot(argument_list)
                Figure_Out = fig.reserve_timeseries()
                Figure_Out["fig"].savefig(reserve_timeseries_figures + region + "_" + row["Figure Output Name"] + "_" + Scenario_name, dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(reserve_timeseries_figures, region + "_" + row["Figure Output Name"] + "_" + Scenario_name + ".csv"))
                
            if row["Figure Type"] == "Reserve Timeseries Facet Grid":
                fig = reserves.mplot(argument_list)
                Figure_Out = fig.reserve_timeseries_facet()
                Figure_Out.savefig(reserve_timeseries_figures + region + "_" + row["Figure Output Name"], dpi=600, bbox_inches='tight')

    else:
        
       
        
        for zone_input in Zones:
            argument_list =  [row.iloc[3], row.iloc[4], row.iloc[5], row.iloc[6],row.iloc[7], row.iloc[8],
                                  hdf_out_folder, zone_input, AGG_BY, ordered_gen, PLEXOS_color_dict, Multi_Scenario,
                                  Scenario_Diff, PLEXOS_Scenarios, ylabels, xlabels, color_list, marker_style, gen_names_dict, pv_gen_cat, 
                                  re_gen_cat, vre_gen_cat, Reserve_Regions]
                                    
            if row["Figure Type"] == "Generation Stack":
                fig = generation_stack.mplot(argument_list) 
                Figure_Out = fig.gen_stack()
                Figure_Out["fig"].savefig(os.path.join(gen_stack_figures, zone_input + "_" + row["Figure Output Name"] + "_" + Scenario_name), dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(gen_stack_figures, zone_input + "_" + row["Figure Output Name"] + "_" + Scenario_name + ".csv"))
                
            elif row["Figure Type"] == "Generation Stack Facet Grid":
                fig = generation_stack.mplot(argument_list) 
                Figure_Out = fig.gen_stack_facet()
                Figure_Out.savefig(os.path.join(gen_stack_figures, zone_input + "_" + row["Figure Output Name"]), dpi=600, bbox_inches='tight')
            
            elif row["Figure Type"] == "Total Generation": 
                fig = total_generation.mplot(argument_list) 
                Figure_Out = fig.total_gen()
                Figure_Out["fig"].figure.savefig(os.path.join(tot_gen_stack_figures, zone_input + "_" + row["Figure Output Name"]), dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(tot_gen_stack_figures, zone_input + "_" + row["Figure Output Name"] + ".csv"))
                
            elif row["Figure Type"] == "Total Generation Facet Grid": 
                fig = total_generation.mplot(argument_list) 
                Figure_Out = fig.total_gen_facet()
                Figure_Out["fig"].savefig(os.path.join(tot_gen_stack_figures, zone_input + "_" + row["Figure Output Name"]), dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(tot_gen_stack_figures, zone_input + "_" + row["Figure Output Name"] + ".csv"))
                
            elif row["Figure Type"] == "Total Installed Capacity":
                fig = total_installed_capacity.mplot(argument_list)
                Figure_Out = fig.total_cap()
                Figure_Out["fig"].figure.savefig(os.path.join(installed_cap_figures, zone_input + "_" + row["Figure Output Name"]) , dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(installed_cap_figures, zone_input + "_" + row["Figure Output Name"] + ".csv"))
                
            elif row["Figure Type"] == "Capacity Factor": 
                fig = capacity_factor.mplot(argument_list)
                Figure_Out = fig.cf()
                Figure_Out["fig"].figure.savefig(os.path.join(capacity_factor_figures, zone_input + "_" + row["Figure Output Name"]) , dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(capacity_factor_figures, zone_input + "_" + row["Figure Output Name"] + ".csv"))
                
            elif row["Figure Type"] == "Average Output When Committed": 
                fig = capacity_factor.mplot(argument_list)
                Figure_Out = fig.avg_output_when_committed()
                Figure_Out["fig"].figure.savefig(os.path.join(capacity_factor_figures, zone_input + "_" + row["Figure Output Name"]) , dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(capacity_factor_figures, zone_input + "_" + row["Figure Output Name"] + ".csv"))
                
            elif row["Figure Type"] == "Capacity Started": 
                fig = ramping.mplot(argument_list)
                Figure_Out = fig.capacity_started()
                Figure_Out["fig"].figure.savefig(os.path.join(ramping_figures, zone_input + "_" + row["Figure Output Name"]) , dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(ramping_figures, zone_input + "_" + row["Figure Output Name"] + ".csv"))     
                
            # Continue here (NSG)
            elif row["Figure Type"] == "Curtailment vs Penetration": 
                fig = curtailment.mplot(argument_list)
                Figure_Out = fig.curt_pen()
                Figure_Out["fig"].savefig(os.path.join(figure_folder, zone_input + "_" + row["Figure Output Name"]) , dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(figure_folder, zone_input + "_" + row["Figure Output Name"] + ".csv"))
            
            elif row["Figure Type"] == "Curtailment Duration Curve": 
                fig = curtailment.mplot(argument_list)
                Figure_Out = fig.curt_duration_curve()
                Figure_Out["fig"].savefig(os.path.join(figure_folder, zone_input + "_" + row["Figure Output Name"]) , dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(figure_folder, zone_input + "_" + row["Figure Output Name"] + ".csv"))
                
            elif row["Figure Type"] == "Production Cost": 
                fig = production_cost.mplot(argument_list)
                Figure_Out = fig.prod_cost()
                Figure_Out["fig"].savefig(os.path.join(system_cost_figures, zone_input + "_" + row["Figure Output Name"]) , dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(system_cost_figures, zone_input + "_" + row["Figure Output Name"] + ".csv"))
                
            elif row["Figure Type"] == "Total System Cost": 
                fig = production_cost.mplot(argument_list)
                Figure_Out = fig.sys_cost()
                Figure_Out["fig"].savefig(os.path.join(system_cost_figures, zone_input + "_" + row["Figure Output Name"]) , dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(system_cost_figures, zone_input + "_" + row["Figure Output Name"] + ".csv"))
                
            elif row["Figure Type"] == "Generation Timeseries Difference": 
                fig = generation_stack.mplot(argument_list) 
                Figure_Out = fig.gen_diff()
                Figure_Out["fig"].savefig(os.path.join(figure_folder, zone_input + "_" + row["Figure Output Name"] + "_" + Scenario_Diff[0]+"_vs_"+Scenario_Diff[1]), dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(figure_folder, zone_input + "_" + row["Figure Output Name"] + "_" + Scenario_Diff[0]+"_vs_"+Scenario_Diff[1] + ".csv"))
        
            elif row["Figure Type"] == "Unserved Energy Timeseries" :
                fig = unserved_energy.mplot(argument_list)
                Figure_Out = fig.unserved_energy_timeseries()
                Figure_Out["fig"].savefig(os.path.join(figure_folder, zone_input + "_" + row["Figure Output Name"]) , dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(figure_folder, zone_input + "_" + row["Figure Output Name"] + ".csv"))
                
            elif row["Figure Type"] == 'Total Unserved Energy': 
                fig = unserved_energy.mplot(argument_list)
                Figure_Out = fig.tot_unserved_energy()
                Figure_Out["fig"].savefig(os.path.join(figure_folder, zone_input + "_" + row["Figure Output Name"]) , dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(figure_folder, zone_input + "_" + row["Figure Output Name"] + ".csv"))
                
            elif row["Figure Type"] == "Generation Unstacked":
                fig = generation_unstack.mplot(argument_list) 
                Figure_Out = fig.gen_unstack()
                Figure_Out["fig"].savefig(os.path.join(gen_stack_figures, zone_input + "_" + row["Figure Output Name"] + "_" + Scenario_name), dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(gen_stack_figures, zone_input + "_" + row["Figure Output Name"] + "_" + Scenario_name + ".csv"))
                
            elif row["Figure Type"] == "Generation Unstacked Facet Grid":
                fig = generation_unstack.mplot(argument_list) 
                Figure_Out = fig.gen_unstack_facet()
                Figure_Out.savefig(os.path.join(gen_stack_figures, zone_input + "_" + row["Figure Output Name"]), dpi=600, bbox_inches='tight')
                
            elif row["Figure Type"] == 'Transmission':
                fig = transmission.mplot(argument_list) 
                Figure_Out = fig.net_interchange()
                Figure_Out["fig"].savefig(os.path.join(transmission_figures, zone_input + "_" + row["Figure Output Name"] + "_" + Scenario_name), dpi=600, bbox_inches='tight')
                Figure_Out["data_table"].to_csv(os.path.join(transmission_figures, zone_input + "_" + row["Figure Output Name"] + "_" + Scenario_name + ".csv"))
                

 #%%               
                