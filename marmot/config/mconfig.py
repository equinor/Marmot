# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 17:44:11 2021

@author: Daniel Levie

This module creates the default config.yml file that is used by Marmot.
The parser function is used to parse information from the config file.
The defaults defined here should not be modifed by any user, 
instead edit the values directly in the config.yml file once created. 
"""

import os
import yaml
from typing import Union

CONFIGFILE_NAME = "config.yml"

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)
configfile_path = os.path.join(dir_path,CONFIGFILE_NAME)


def createConfig(configfile_path: str):
    """Creates config.yml file using default values.

    The following are Marmot default config settings that are used to 
    create the config.yml file when Marmot is first run.
    Users Should NOT edit these values, instead edit the values directly 
    in the config.yml file once created. If the config.yml file is deleted, 
    it will be created with these defaults when mconfig.py is called anytime Marmot
    is run. 

    Args:
        configfile_path (str): Path to config.yml file
    """
    data = dict(
        
        font_settings = dict(
            xtick_size = 12,
            ytick_size = 12,
            axes_label_size = 16,
            legend_size = 12,
            title_size = 16,
            font_family = 'serif'
            ),
        
        text_position = dict(
            title_height = 40
            ),
        
        figure_size = dict(
            xdimension = 6,
            ydimension = 4),
        
        axes_options = dict(
            x_axes_minticks = 4,
            x_axes_maxticks = 8,
            y_axes_decimalpt = 1),
        
        axes_label_options = dict(
            rotate_x_labels = True,
            rotate_at_num_labels = 7,
            rotation_angle = 45),
        
        plot_data = dict(
            curtailment_property = 'Curtailment',
            include_total_pumped_load_line = True,
            include_timeseries_pumped_load_line = True),

        figure_file_format = 'svg',
        
        shift_leapday = False,
        skip_existing_properties = True,
        auto_convert_units = True,
        plot_title_as_region = True,
        
        user_defined_inputs_file = 'Marmot_user_defined_inputs.csv',

        plot_select_file = 'Marmot_plot_select.csv',

        plexos_properties_file = 'plexos_properties.csv',
        
        color_dictionary_file = 'colour_dictionary.csv',
        ordered_gen_categories = 'ordered_gen_categories.csv'
        )

    with open(configfile_path, "w") as cfgfile:
        yaml.safe_dump(data, cfgfile,default_flow_style=False, sort_keys=False)


# Check if there is already a configuration file
if not os.path.isfile(configfile_path):
    # Create the configuration file as it doesn't exist yet
    createConfig(configfile_path)
    
    
def parser(top_level: str, second_level: str = None) -> Union[dict, str, int, float]: 
    """Pull requested value from config.yml file

    Args:
        top_level (str): Top level of config dictionary, 
            will return specified level and any sublevel.
        second_level (str, optional): Second level of config dictionary 
            under top_level, will return a single value. 
            Defaults to None.

    Returns:
        Union[dict, str, int, float]: Returns the requested level 
            or value from the config file. Return type varies based on
            on level accessed.
    """
    with open(configfile_path, "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile.read())
    
    if not second_level:
        value = cfg[top_level]
    else:
        value = cfg[top_level][second_level]
    return value 
    

def edit_value(new_value: str, top_level: str, 
               second_level: str = None):
    """Edit the config.yml file through code

    Args:
        new_value (str): New value to apply to config file.
        top_level (str): Top level of config dictionary, 
            will return specified level and any sublevel.
        second_level (str, optional): Second level of config dictionary under top_level, 
            will return a single value. 
            Defaults to None.
    """
    with open(configfile_path, "r") as f:
        cfg = yaml.safe_load(f)
    
    if not second_level:
        cfg[top_level] = new_value
    else:
        cfg[top_level][second_level] = new_value  
            
    with open(configfile_path,'w') as f:
            yaml.safe_dump(cfg,f,default_flow_style=False, sort_keys=False)
            

def reset_defaults():   
    """When called, resets config.yml to default values
    """
    createConfig(configfile_path)

