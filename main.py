import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from csa_functions import *

case_name = 'sfe_tbs_M1_025'
version = 'vv3'

case_name = 'sfe_tbs_M1_024'
version = 'vv3'

interval = 5
station_length = 40

water_depth = 0.5

"""
method = 'const_slope' 
method_param = [0.011770794, 0.246309559]
    # For 'const_slope', method_param = [slope, water depth at x=0]
"""
"""
method = 'vertical_offset' 
method_param = 0.1
    # For 'vertical_offset', method_param = vertical offset
"""

method = 'max_width_diff'
method_param = 14.68022043 # for SFE 24
method_param = 5

    # For 'max_width_diff', method_param = bankfull discharge (cms)

figure_xsect = 1

min_elev = 300
max_slope = 20

#################################################################
water_depth_str = "%.2f" % water_depth
water_depth_str = water_depth_str.replace('.','p')
case_name_v = case_name + '_' + version

if version == '':
    int_len = str(interval) + 'm_' + str(station_length) + 'm'
    int_len_depth_method = str(interval) + 'm_' + str(station_length) + 'm_' + water_depth_str + 'm_' + method
    path_xsect = './' + case_name + '/' + 'thalweg_' + int_len + '.shp'
    path_terrains = ['./' + case_name + '/' + case_name + '.tif']

else:
    int_len = str(interval)+'m_'+str(station_length)+'m'
    int_len_depth_method = str(interval)+'m_'+str(station_length)+'m_'+water_depth_str+'m_'+method
    path_xsect = './'+case_name_v+'/'+case_name_v+'/thalweg_'+int_len+'.shp'
    path_terrains = ['./'+case_name_v+'/'+case_name_v+'/'+case_name_v+'.tif']
    #path_xsect = './sfe322/thalweg_'+int_len+'.shp'
    #path_terrains = ['./sfe322/'+case_name_v+'.tif']

Execute_StackProfile_3d = 1
unit = 'SI'

Line_IDs, bed_stage_width_df = csa_functions(path_xsect, interval, path_terrains, water_depth, min_elev, max_slope,
                                                int_len_depth_method, Execute_StackProfile_3d, figure_xsect, unit, method, method_param)

x_dist = Line_IDs*interval

#if x_from_upstream == 0:
#    x_dist_from_upstream = max(x_dist) - x_dist
#else:
#    x_dist_from_upstream = x_dist

if not os.path.exists(os.path.dirname(path_terrains[0]) + '/GVFs'):
    os.mkdir(os.path.dirname(path_terrains[0]) + '/GVFs')

#x_dist = x_dist[::-1]
plt.figure(figsize=(12, 6))
plt.plot(x_dist, bed_stage_width_df.iloc[:, 2], label='width')
plt.xlabel('Longitudinal distance (m)')
plt.ylabel('Width series at depth = ' + str(water_depth) + ' m (m)')
plt.legend()
plt.savefig(os.path.dirname(path_terrains[0]) + '/GVFs/width_' + int_len_depth_method)

plt.figure(figsize=(12, 6))
plt.plot(x_dist, bed_stage_width_df.iloc[:, 0], '-', label='Thalweg profile')
plt.plot(x_dist, bed_stage_width_df.iloc[:, 1], '-', label='Water stage')
plt.xlabel('Longitudinal distance (m)')
plt.ylabel('Thalweg bed profile and water stage (m)')
plt.legend()
plt.savefig(os.path.dirname(path_terrains[0]) + '/GVFs/profiles_' + int_len_depth_method)

path_xlsx = os.path.dirname(path_terrains[0])+'/GVFs/width_' + int_len_depth_method + '.xlsx'
tmp = np.transpose(np.array([x_dist]))
tmp_stack = np.hstack([tmp, bed_stage_width_df])
df = pd.DataFrame(data=tmp_stack, columns=['x_dist','bed_profile', 'water_stage','width', 'nan'])
df.to_excel(path_xlsx)