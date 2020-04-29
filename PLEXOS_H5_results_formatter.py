# -*- coding: utf-8 -*-
"""
Created on Wed May 22 14:29:48 2019

@author: Daniel Levie

This code was written to process PLEXOS HDF5 outputs to get them ready for plotting. 
Once the data is processed it is outputed as an intermediary HDF5 file format so that 
it can be read into the Marmot_results_plotting.py file

"""

#===============================================================================
# Import Python Libraries
#===============================================================================

import pandas as pd
import numpy as np
import os
import h5py
import sys
import pathlib
import time

sys.path.append('../h5plexos')
from h5plexos.query import PLEXOSSolution

try:
    print("Will process row:" +(sys.argv[1]))
    print(str(len(sys.argv)-1)+" arguments were passed from commmand line.")
except IndexError:
    #No arguments passed
    pass
#===============================================================================
# Create HDF5 file from PLEXOS zip solution
#===============================================================================
#This is only required if your output has not been processed already on Eagle

# from h5plexos.process import process_solution
# PLEXOS_Solution = '/Volumes/PLEXOS CEII/Projects/Extreme Events/Model c_Feb01-04_2011_2024 Solution/Model c_Feb01-04_2011_2024 Solution.zip' #PLEXOS solution .zip file.
# process_solution(PLEXOS_Solution,'/Volumes/PLEXOS CEII/Projects/Extreme Events/Model c_Feb01-04_2011_2024 Solution/Model c_Feb01-04_2011_2024 Solution.h5') # Saves out to PLEXOS_Solution.h5

#===============================================================================
# Load Input Properties
#===============================================================================

#A bug in pandas requires this to be included, otherwise df.to_string truncates long strings
#Fix available in Pandas 1.0 but leaving here in case user version not up to date
pd.set_option("display.max_colwidth", 1000)

#changes working directory to location of this python file
os.chdir(pathlib.Path(__file__).parent.absolute())

Marmot_user_defined_inputs = pd.read_csv('Marmot_user_defined_inputs.csv', usecols=['Input','User_defined_value'], 
                                         index_col='Input', skipinitialspace=True)

# File which determiens which plexos properties to pull from the h5plexos results and process, this file is in the repo
Plexos_Properties = pd.read_csv('plexos_properties.csv')

# Name of the Scenario(s) being run, must have the same name(s) as the folder holding the runs HDF5 file
Scenario_List = pd.Series(Marmot_user_defined_inputs.loc['Scenario_process_list'].squeeze().split(",")).str.strip().tolist()

# The folder that contains all PLEXOS h5plexos outputs - the h5 files should be contained in another folder with the Scenario_name
PLEXOS_Solutions_folder = Marmot_user_defined_inputs.loc['PLEXOS_Solutions_folder'].to_string(index=False).strip()

# Folder to save your processed solutions
Processed_Solutions_folder = Marmot_user_defined_inputs.loc['Processed_Solutions_folder'].to_string(index=False).strip()

# This folder contains all the csv required for mapping and selecting outputs to process
# Examples of these mapping files are within the Marmot repo, you may need to alter these to fit your needs
Mapping_folder = 'mapping_folder'

Region_Mapping = pd.read_csv(os.path.join(Mapping_folder, Marmot_user_defined_inputs.loc['Region_Mapping.csv_name'].to_string(index=False).strip()))
reserve_region_type = pd.read_csv(os.path.join(Mapping_folder, Marmot_user_defined_inputs.loc['reserve_region_type.csv_name'].to_string(index=False).strip()))
gen_names = pd.read_csv(os.path.join(Mapping_folder, Marmot_user_defined_inputs.loc['gen_names.csv_name'].to_string(index=False).strip()))

# number of hours overlapped between two adjacent models
overlap = pd.to_numeric(Marmot_user_defined_inputs.loc['overlap'].to_string(index=False)) 

# Value of Lost Load for calculatinhg cost of unserved energy
VoLL = pd.to_numeric(Marmot_user_defined_inputs.loc['VoLL'].to_string(index=False))  



#===============================================================================
# Standard Naming of Generation Data
#===============================================================================

gen_names_dict=gen_names[['Original','New']].set_index("Original").to_dict()["New"]
vre_gen_cat = pd.read_csv(os.path.join(Mapping_folder, 'vre_gen_cat.csv'),squeeze=True).str.strip().tolist()

#===============================================================================
# Region mapping
#===============================================================================

try:
    Region_Mapping = Region_Mapping.drop(["category"],axis=1) # delete category columns if exists
except Exception:
    pass

#=============================================================================
# FUNCTIONS FOR PLEXOS DATA EXTRACTION
#=============================================================================
    

# Function for formating data which comes from the PLEXOS Region Category
def df_process_region(df, overlap_hour): 
    df = df.reset_index() # unzip the levels in index
    df.rename(columns={'name':'region'}, inplace=True)
    if Region_Mapping.empty==False: #checks if Region_Maping contains data to merge, skips if empty (Default)
        df = df.merge(Region_Mapping, how='left', on='region') # Merges in all Region Mappings
    df = df.drop(["band", "property", "category"],axis=1) 
    df_col = list(df.columns) # Gets names of all columns in df and places in list
    df_col.remove(0) # Removes 0, the data column from the list 
    df_col.insert(0, df_col.pop(df_col.index("timestamp"))) #move timestamp to start of df
    df =  df.groupby(df_col).sum() #moves all columns to multiindex except 0 column
    return df   

# Function for formating data which comes from the PLEXOS Region Category
def df_process_zone(df, overlap_hour): 
    df = df.reset_index() # unzip the levels in index
    df.rename(columns={'name':'zone'}, inplace=True)
    df = df.drop(["band", "property", "category"],axis=1) 
    df_col = list(df.columns) # Gets names of all columns in df and places in list
    df_col.remove(0) # Removes 0, the data column from the list 
    df_col.insert(0, df_col.pop(df_col.index("timestamp"))) #move timestamp to start of df
    df =  df.groupby(df_col).sum() #moves all columns to multiindex except 0 column
    return df    

# Function for formatting data which comes form the PLEXOS Generator Category
def df_process_gen(df, overlap_hour): 
    df = df.reset_index() # unzip the levels in index
    df = df.drop(["band", "property"],axis=1) 
    df.rename(columns={'category':'tech', 'name':'gen_name'}, inplace=True)
    if region_generators.empty==False: #checks if region_generators contains data to merge, skips if empty
        df = df.merge(region_generators, how='left', on='gen_name') # Merges in regions where generators are located
    if zone_generators.empty==False: #checks if zone_generators contains data to merge, skips if empty
        df = df.merge(zone_generators, how='left', on='gen_name') # Merges in zones where generators are located
    if Region_Mapping.empty==False: #checks if Region_Maping contains data to merge, skips if empty (Default)
        df = df.merge(Region_Mapping, how='left', on='region') # Merges in all Region Mappings
    df['tech'] = df['tech'].map(lambda x: gen_names_dict.get(x,x))
    df_col = list(df.columns) # Gets names of all columns in df and places in list
    df_col.remove(0) # Removes 0, the data column from the list 
    df_col.insert(0, df_col.pop(df_col.index("timestamp"))) #move timestamp to start of df
    df =  df.groupby(df_col).sum() #moves all columns to multiindex except 0 column 
    return df  

# Function for formatting data which comes form the PLEXOS Line Category
def df_process_line(df, overlap_hour): 
    df = df.reset_index() # unzip the levels in index
    df = df.drop(["band", "property", "category"],axis=1) # delete property and band columns
    df.rename(columns={'name':'line_name'}, inplace=True)
    df = df.groupby(["timestamp", "line_name"]).sum()
    return df 

# Function for formatting data which comes form the PLEXOS Line Category
def df_process_interface(df, overlap_hour): 
    df = df.reset_index() # unzip the levels in index
    df = df.drop(["band", "property"],axis=1) # delete property and band columns
    df.rename(columns={'category':'region_region', 'name':'line_name'}, inplace=True)
    df = df.groupby(["timestamp",  "region_region", "line_name"]).sum()
    return df                   

# Function for formatting data which comes form the PLEXOS Reserve Category
def df_process_reserve(df, overlap_hour): 
    df = df.reset_index() # unzip the levels in index
    df = df.drop(["band", "property", "category"],axis=1) # delete property and band columns
    df.rename(columns={'name':'parent'}, inplace=True)
    df = df.merge(reserve_region_type, how='left', on='parent')
    df = df.groupby(["timestamp",  "Reserve_Region", "Type"]).sum()
    return df      

# Function for formatting data which comes form the PLEXOS Reserve_generators Category
def df_process_reserve_generators(df, overlap_hour): 
    df = df.reset_index() # unzip the levels in index
    df = df.drop(["band", "property"],axis=1) # delete property and band columns
    df.rename(columns={'child':'gen_name'}, inplace=True)
    df = df.merge(generator_category, how='left', on='gen_name')
    df = df.merge(reserve_region_type, how='left', on='parent')
    df['tech'] = df['tech'].map(lambda x: gen_names_dict.get(x,x))   
    df = df.groupby(["timestamp",  "tech", "Reserve_Region", "Type"]).sum()
    return df      

# Function for formatting data which comes form the PLEXOS Fuel Category
def df_process_fuel(df, overlap_hour): 
    df = df.reset_index() # unzip the levels in index
    df = df.drop(["band", "property", "category"],axis=1) # delete property and band columns
    df.rename(columns={'name':'fuel_type'}, inplace=True)
    df = df.groupby(["timestamp",  "fuel_type"]).sum()
    return df   

# Function for formatting data which comes form the PLEXOS Constraint Category
def df_process_constraint(df, overlap_hour): 
    df = df.reset_index() # unzip the levels in index
    df = df.drop(["band", "property"],axis=1) # delete property and band columns
    df.rename(columns={'category':'constraint_category', 'name':'constraint'}, inplace=True)
    df = df.groupby(["timestamp",  "constraint_category", "constraint"]).sum()
    return df

# Function for formatting data which comes form the PLEXOS emission Category
def df_process_emission(df, overlap_hour): 
    df = df.reset_index() # unzip the levels in index
    df = df.drop(["band", "property"],axis=1) # delete property and band columns
    df.rename(columns={'name':'emission_type'}, inplace=True)
    df = df.groupby(["timestamp", "emission_type"]).sum()
    return df 

# Function for formatting data which comes form the PLEXOS storage Category
def df_process_storage(df, overlap_hour): 
    df = df.reset_index() # unzip the levels in index
    df = df.drop(["band", "property", "category"],axis=1) # delete property and band columns
    df = df.merge(generator_storage, how='left', on='name')
    if region_generators.empty==False: #checks if region_generators contains data to merge, skips if empty
        df = df.merge(region_generators, how='left', on='gen_name') # Merges in regions where generators are located
    if zone_generators.empty==False: #checks if zone_generators contains data to merge, skips if empty
        df = df.merge(zone_generators, how='left', on='gen_name') # Merges in zones where generators are located
    if Region_Mapping.empty==False: #checks if Region_Maping contains data to merge, skips if empty (Default)
        df = df.merge(Region_Mapping, how='left', on='region') # Merges in all Region Mappings
    df.rename(columns={'name':'storage_resource'}, inplace=True)
    df_col = list(df.columns) # Gets names of all columns in df and places in list
    df_col.remove(0) # Removes 0, the data column from the list 
    df_col.insert(0, df_col.pop(df_col.index("timestamp"))) #move timestamp to start of df
    df =  df.groupby(df_col).sum() #moves all columns to multiindex except 0 column 
    return df

# Function for formatting data which comes form the PLEXOS region_regions Category
def df_process_region_regions(df, overlap_hour): 
    df = df.reset_index() # unzip the levels in index
    df = df.drop(["band", "property"],axis=1) # delete property and band columns
    df =  df.groupby(["timestamp",  "parent", "child"]).sum()
    return df                                          


# This fucntion prints a warning message when the get_data function cannot find the specified property in the H5plexos hdf5 file
def report_prop_error(prop,loc):
        print('CAN NOT FIND {} FOR {}. {} DOES NOT EXIST'.format(prop,loc,prop))
        df = pd.DataFrame()
        return df



# This function handles the pulling of the data from the H5plexos hdf5 file and then passes the data to one of the formating functions                
def get_data(loc, prop,t, db, overlap):
    if loc == 'constraint': 
        try: 
            df = db.constraint(prop, timescale=t)
        except KeyError: 
            df = report_prop_error(prop,loc)
            return df
        df = df_process_constraint(df, overlap)
        return df
        
        
    elif loc == 'emission':
        try: 
            df = db.emission(prop, timescale=t)
        except KeyError: 
            df = report_prop_error(prop,loc)
            return df
        df = df_process_emission(df, overlap)
        return df
        
        
#    elif loc == 'emission_generators':
#        try: 
#            df = db.emission_generators(prop, timescale=t)
#        except KeyError: df = report_prop_error(prop,loc)
        
    elif loc == 'fuel':
        try: 
            df = db.fuel(prop, timescale=t)
        except KeyError: 
            df = report_prop_error(prop,loc)
            return df        
        df = df_process_fuel(df, overlap)
        return df
        
    elif loc == 'generator':
        try:
            df = db.generator(prop, timescale=t)
        except KeyError: 
            df = report_prop_error(prop,loc)
            return df
        df = df_process_gen(df, overlap)
        # Checks if all generator tech categorieses have been identified and matched. If not, lists categories that need a match
        if set(df.index.unique(level="tech")).issubset(gen_names["New"].unique()) == False:
            print("\n WARNING!! The Following Generators do not have a correct category mapping:")
            missing_gen_cat = list((set(df.index.unique(level="tech"))) - (set(gen_names["New"].unique())))
            print(missing_gen_cat)
            print("")
        return df
        
    elif loc == 'line':
        try: 
            df = db.line(prop, timescale=t)
        except KeyError: 
            df = report_prop_error(prop,loc)
            return df
        df = df_process_line(df, overlap)
        return df
       
       
    elif loc == 'interface':
        try: 
            df = db.line(prop, timescale=t)
        except KeyError: 
            df = report_prop_error(prop,loc)
            return df
        df = df_process_interface(df, overlap)
        return df
        
    elif loc == 'region':
        try: 
            df = db.region(prop, timescale=t)
        except KeyError: 
            df = report_prop_error(prop,loc)
            return df
        df = df_process_region(df, overlap)
        if prop == "Unserved Energy" and int(df.sum(axis=0)) > 0:
            print("\n WARNING! Scenario contains Unserved Energy: " + str(int(df.sum(axis=0))) + " MW\n")
        return df
        
    elif loc == 'reserve':
        try: 
            df = db.reserve(prop, timescale=t)
        except KeyError: 
            df = report_prop_error(prop,loc)
            return df
        df = df_process_reserve(df, overlap) 
        return df
        
    elif loc == 'reserve_generators':
        try: 
            df = db.reserve_generators(prop, timescale=t)
        except KeyError: 
            df = report_prop_error(prop,loc)
            return df
        df = df_process_reserve_generators(df, overlap) 
        return df
        
    elif loc == 'storage':
        try: 
            df = db.storage(prop, timescale=t)
        except KeyError: 
            df = report_prop_error(prop,loc)
            return df
        df = df_process_storage(df, overlap) 
        return df
        
    elif loc == 'region_regions':
        try: 
            df = db.region_regions(prop, timescale=t)
        except KeyError: 
            df = report_prop_error(prop,loc)
            return df
        df = df_process_region_regions(df, overlap) 
        return df
        
    elif loc == 'zone':
        try:
            df = db.zone(prop, timescale=t)
        except KeyError: 
            df = report_prop_error(prop,loc)
            return df
        df = df_process_zone(df, overlap)
        return df
        
    else: 
        df = pd.DataFrame()
        print('{} NOT RETRIEVED.\nNO H5 CATEGORY: {}'.format(prop,loc))


#===================================================================================
# Main         
#=================================================================================== 
        
for Scenario_name in Scenario_List:
    
    print("\n#### Processing " + Scenario_name + " PLEXOS Results ####")
    
    #===============================================================================
    # Input and Output Directories 
    #===============================================================================
    
    HDF5_output = Scenario_name + "_formatted.h5"
    
    PLEXOS_Scenarios = os.path.join(Processed_Solutions_folder, Scenario_name)
    try:
        os.makedirs(PLEXOS_Scenarios)
    except FileExistsError:
        # directory already exists
        pass
    hdf_out_folder = os.path.join(PLEXOS_Scenarios, 'Processed_HDF5_folder')
    try:
        os.makedirs(hdf_out_folder)
    except FileExistsError:
        # directory already exists
        pass
    HDF5_folder_in = os.path.join(PLEXOS_Solutions_folder, Scenario_name)
    try:
        os.makedirs(HDF5_folder_in)
    except FileExistsError:
        # directory already exists
        pass
    figure_folder = os.path.join(PLEXOS_Scenarios, 'Figures_Output')
    try:
        os.makedirs(figure_folder)
    except FileExistsError:
        # directory already exists
        pass
    
    startdir=os.getcwd()
    os.chdir(HDF5_folder_in)     #Due to a bug on eagle need to chdir before listdir
    files = sorted(os.listdir()) # List of all files in hdf5 folder in alpha numeric order
    os.chdir(startdir)
    
    files_list = []
    for names in files:
        if names.endswith(".h5"):
            files_list.append(names) # Creates a list of only the hdf5 files
    
    hdf5_read = os.path.join(HDF5_folder_in, files_list[0]) #The first file is used for metadata.
    
    data = h5py.File(hdf5_read, 'r')
    metadata = np.asarray(data['metadata'])
    
    
    try:
        # Region generators mapping
        region_generators = pd.DataFrame(np.asarray(data['metadata/relations/region_generators']))
        region_generators.rename(columns={'child':'gen_name'}, inplace=True)
        region_generators.rename(columns={'parent':'region'}, inplace=True)
        region_generators["gen_name"]=region_generators["gen_name"].str.decode("utf-8")
        region_generators["region"]=region_generators["region"].str.decode("utf-8")
        region_generators.drop_duplicates(subset=["gen_name"],keep='first',inplace=True) #For generators which belong to more than 1 region, drop duplicates.
    except KeyError:
        region_generators = pd.DataFrame()
        print("\Regional data not included in h5plexos results.\nSkipping Regional properties\n")
    
    
    try:
        # Zone generators mapping
        zone_generators = pd.DataFrame(np.asarray(data['metadata/relations/zone_generators']))
        zone_generators.rename(columns={'child':'gen_name'}, inplace=True)
        zone_generators.rename(columns={'parent':'zone'}, inplace=True)
        zone_generators["gen_name"]=zone_generators["gen_name"].str.decode("utf-8")
        zone_generators["zone"]=zone_generators["zone"].str.decode("utf-8")
        zone_generators.drop_duplicates(subset=["gen_name"],keep='first',inplace=True) #For generators which belong to more than 1 region, drop duplicates.
        
        # Outputs Zones in results to pickle file
        zones = pd.DataFrame(np.asarray(data['metadata/objects/zone']))
        zones["name"]=zones["name"].str.decode("utf-8")
        zones["category"]=zones["category"].str.decode("utf-8")
        zones.to_pickle('zones.pkl')
    
    except KeyError:
        zone_generators = pd.DataFrame()
        print("\nZonal data not included in h5plexos results.\nSkipping Zonal properties\n")
        
    # Generator categories mapping 
    generator_category = pd.DataFrame(np.asarray(data['metadata/objects/generator']))
    generator_category.rename(columns={'name':'gen_name'}, inplace=True)
    generator_category.rename(columns={'category':'tech'}, inplace=True)
    generator_category["gen_name"]=generator_category["gen_name"].str.decode("utf-8")
    generator_category["tech"]=generator_category["tech"].str.decode("utf-8")
    
    
    try:
        # Generator head and tail torage mapping
        generator_headstorage = pd.DataFrame(np.asarray(data['metadata/relations/generator_headstorage']))
        generator_tailtorage = pd.DataFrame(np.asarray(data['metadata/relations/generator_tailstorage']))
        generator_storage = pd.concat([generator_headstorage, generator_tailtorage])
        generator_storage.rename(columns={'child':'name'}, inplace=True)
        generator_storage.rename(columns={'parent':'gen_name'}, inplace=True)
        generator_storage["name"]=generator_storage["name"].str.decode("utf-8")
        generator_storage["gen_name"]=generator_storage["gen_name"].str.decode("utf-8")
    except KeyError:
        generator_storage = pd.DataFrame()
        print("\nGenerator head/tail storage not included in h5plexos results.\nSkipping storage property\n")
    
    # If Region_Mapping csv was left empty, regions will be retrieved from the plexos results h5 file for use in Marmot_plot.
    # This limits the user to only plotting results from PLEXOS regions, therefore it is recommended to populate the Region_Mapping.csv for more control. 
    if Region_Mapping.empty==True:
        regions = pd.DataFrame(np.asarray(data['metadata/objects/region']))
        regions["name"]=regions["name"].str.decode("utf-8")
        regions["category"]=regions["category"].str.decode("utf-8")
        regions.to_pickle('regions.pkl')
    
    ## Get Line relations and save to pickle 
    try:
        line_relations=pd.DataFrame(np.asarray(data['metadata/objects/line']))
        line_relations["name"]=line_relations["name"].str.decode("utf-8")
        line_relations["category"]=line_relations["category"].str.decode("utf-8")
        line_relations.to_pickle(PLEXOS_Scenarios+"/line_relations.pkl")
    except KeyError:
        print("\nLine data not included in h5plexos results.\nSkipping Line property\n")
        
        
    # Read in all HDF5 files into dictionary 
    print("Loading all HDF5 files to prepare for processing")
    hdf5_collection = {}
    for file in files_list:
        hdf5_collection[file] = PLEXOSSolution(os.path.join(HDF5_folder_in, file))
    
    
    ######### Process the Outputs################################################          
    
    
    # Creates Initial HDF5 file for ouputing formated data
    Processed_Data_Out=pd.DataFrame()
    if os.path.isfile(os.path.join(hdf_out_folder,HDF5_output))==True:
        print("Warning: "+hdf_out_folder + "/" + HDF5_output+" already exists; new variables will be added.\n")
    else:
        Processed_Data_Out.to_hdf(os.path.join(hdf_out_folder, HDF5_output), key= "generator_Generation" , mode="w", complevel=9, complib  ='blosc:zlib')
    
    # Filters for chosen Plexos properties to process
    if (len(sys.argv)-1) == 1: # If passed one argument (not including file name which is automatic)
        print("Will process row " +(sys.argv[1])+" of plexos properties regardless of T/F.")
        Plexos_Properties = Plexos_Properties.iloc[int(sys.argv[1])-1].to_frame().T
    else:
        Plexos_Properties = Plexos_Properties.loc[Plexos_Properties["collect_data"] == True]
    
    start = time.time()
    
    # Main loop to process each ouput and pass data to functions
    for index, row in Plexos_Properties.iterrows():
        
        Processed_Data_Out = pd.DataFrame()
        print("Processing " + row["group"] + " " + row["data_set"])
        for model in files_list:
            print("     "+ model) 
            db = hdf5_collection.get(model)
            
            processed_data = get_data(row["group"], row["data_set"], 
                                             row["data_type"], db, overlap)
            if processed_data.empty == True:
                print("\n")
                break
            
            if row["data_type"] == "year":
                Processed_Data_Out = pd.concat([Processed_Data_Out, processed_data*row["unit_multiplier"]])
            else:
                Processed_Data_Out = pd.concat([Processed_Data_Out, processed_data])
                
        if Processed_Data_Out.empty == False:
            if row["data_type"]== "year":
                print("test")
                data_index=Processed_Data_Out.index.names
                Processed_Data_Out_var=Processed_Data_Out.groupby(data_index).var()
                if ('tech' in Processed_Data_Out.index.names) == True: #Remove hydro if tech included
                    Processed_Data_Out_var=Processed_Data_Out_var.drop('Hydro',level='tech')
                if Processed_Data_Out_var[0].max() > 0.0:
                    print("Property "+ row["group"] + " " + row["data_set"]+" "+row["data_type"]+" is summed across partitions if there are multiple partitions.")
                    Processed_Data_Out=Processed_Data_Out.groupby(data_index).sum()    #if the variance is non zero, group by all the values in the index and sum()
                else:
                    print("Property "+ row["group"] + " " + row["data_set"]+" "+row["data_type"]+" is reported by maximum if there are multiple paritions.")
                    Processed_Data_Out=Processed_Data_Out.groupby(data_index).max()
            else:
                oldsize=Processed_Data_Out.size
                Processed_Data_Out = Processed_Data_Out.loc[~Processed_Data_Out.index.duplicated(keep='first')] #Remove duplicates; keep first entry^M
                if  (oldsize-Processed_Data_Out.size) >0:
                    print('Drop duplicates removed '+str(oldsize-Processed_Data_Out.size)+' rows.')
            
            row["data_set"] = row["data_set"].replace(' ', '_')
            try:
                Processed_Data_Out.to_hdf(os.path.join(hdf_out_folder, HDF5_output), key= row["group"] + "_" + row["data_set"], mode="a", complevel=9, complib = 'blosc:zlib')
            except:
                print("File is probably in use, waiting to attempt save for a second time.")
                time.sleep(30)
                try:
                     Processed_Data_Out.to_hdf(os.path.join(hdf_out_folder, HDF5_output), key= row["group"] + "_" + row["data_set"], mode="a", complevel=9, complib = 'blosc:zlib')
                     print("File save succeded on second attempt.")
                except:
                    print("File is probably in use, waiting to attempt save for a third time.")
                    time.sleep(60)
                    try:
                        Processed_Data_Out.to_hdf(os.path.join(hdf_out_folder, HDF5_output), key= row["group"] + "_" + row["data_set"], mode="a",  complevel=9, complib = 'blosc:zlib')
                        print("File save succeded on third attempt.")
                    except:
                        print("Save failed on third try; will not attempt again.")
            del Processed_Data_Out
        else:
            continue
    
    ######### Calculate Extra Ouputs################################################
    try:
        print("Processing generator Curtailment")  
        try:
            Avail_Gen_Out = pd.read_hdf(os.path.join(hdf_out_folder, HDF5_output), 'generator_Available_Capacity')
            Total_Gen_Out = pd.read_hdf(os.path.join(hdf_out_folder, HDF5_output), 'generator_Generation')
            if Total_Gen_Out.empty==True:
                print("WARNING!! generator_Available_Capacity & generator_Generation are required for Curtailment calculation")
        except KeyError:
            print("WARNING!! generator_Available_Capacity & generator_Generation are required for Curtailment calculation")
        # Adjust list of values to drop from vre_gen_cat depending on if it exhists in processed techs
        vre_gen_cat = [name for name in vre_gen_cat if name in Avail_Gen_Out.index.unique(level="tech")]
        
        if not vre_gen_cat:
            print("\nvre_gen_cat is not set up correctly with your gen_names")
            print("To Process Curtailment add correct names to vre_gen_cat.csv")
            print("For more information see Marmot Readme under 'Mapping Files'")
        # Output Curtailment# 
        Curtailment_Out =  ((Avail_Gen_Out.loc[(slice(None), vre_gen_cat),:]) - 
                            (Total_Gen_Out.loc[(slice(None), vre_gen_cat),:]))
        
        Curtailment_Out.to_hdf(os.path.join(hdf_out_folder, HDF5_output), key="generator_Curtailment", mode="a", complevel=9, complib = 'blosc:zlib')
        
    
        #Clear Some Memory
        del Total_Gen_Out
        del Avail_Gen_Out
        del Curtailment_Out
    except Exception:
        print("NOTE!! Curtailment not calculated, processing skipped\n")
        pass
    
    try:
        print("Calculating Cost Unserved Energy: Regions")  
        Cost_Unserved_Energy = pd.read_hdf(os.path.join(hdf_out_folder, HDF5_output), 'region_Unserved_Energy')
        Cost_Unserved_Energy = Cost_Unserved_Energy * VoLL 
        Cost_Unserved_Energy.to_hdf(os.path.join(hdf_out_folder, HDF5_output), key="region_Cost_Unserved_Energy", mode="a", complevel=9, complib = 'blosc:zlib')
    except KeyError:
        print("NOTE!! Regional Unserved Energy not available to process, processing skipped\n")
        pass
    
    try:
        print("Calculating Cost Unserved Energy: Zones")  
        Cost_Unserved_Energy = pd.read_hdf(os.path.join(hdf_out_folder, HDF5_output), 'zone_Unserved_Energy')
        Cost_Unserved_Energy = Cost_Unserved_Energy * VoLL 
        Cost_Unserved_Energy.to_hdf(os.path.join(hdf_out_folder, HDF5_output), key="zone_Cost_Unserved_Energy", mode="a", complevel=9, complib = 'blosc:zlib')
    except KeyError:
        print("NOTE!! Zonal Unserved Energy not available to process, processing skipped\n")
        pass
    
    end = time.time()
    elapsed = end - start
    print('Main loop took ' + str(elapsed/60) + ' minutes.')
    
    ###################################################################            
    
 #test = pd.read_hdf(os.path.join(hdf_out_folder, HDF5_output), 'region_Load')

# Stacked_Gen_read = Stacked_Gen_read.reset_index() # unzip the levels in index
# Stacked_Gen_read.rename(columns={'name':'zone'}, inplace=True)
#         Stacked_Gen_read = Stacked_Gen_read.drop(["band", "property", "category"],axis=1) 
    # if int(Stacked_Gen_read.sum(axis=0)) >= 0:
    #     print("WARNING! Scenario contains Unserved Energy: " + str(int(Stacked_Gen_read.sum(axis=0))) + "MW")

    #storage = db.storage("Generation")
    #storage = df_process_storage(storage, overlap)
