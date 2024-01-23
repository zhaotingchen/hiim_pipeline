#containermpi, NODE, config.ini, 0
import glob
import sys
import os
import numpy as np
import re
from casatasks import mstransform
import configparser

def strlist_to_str(inp):
    out = ''
    for vals in inp:
        out += vals+','
    out = out[:-1]
    return out

def unravel_list(inp):
    out = [item for sublist in inp for item in sublist]
    return out

config_file = sys.argv[-1]
config = configparser.ConfigParser()
config.read(config_file)

hiimtool = config['FILE']['hiimtool']
sys.path.append(hiimtool)
from hiimtool.config_util import tidy_config_path
from hiimtool.ms_tool import get_chanfreq,get_nscan
config = tidy_config_path(config)

work_dir = config['FILE']['work_dir']
sys.path.append(work_dir)
from config import *

mymms = FILE_working_ms
bp_scan = np.sort(unravel_list(CAL_1GC_PRIMARY_SCAN)).tolist()
p_scan = np.sort(unravel_list(CAL_1GC_SECONDARY_SCAN)).tolist()
scan_sort = np.argsort(bp_scan+p_scan)
g_scan = np.sort(bp_scan+p_scan).tolist()

target_field = [field for field in CAL_1GC_FIELD_NAMES if field not in (CAL_1GC_PRIMARY_NAME+CAL_1GC_SECONDARY_NAME)][0]
outmms = FILE_working_ms[:-4]+'_'+target_field+'.mms'
nscan = get_nscan(mymms)
scan_list = ['%04i' % i for i in range(nscan)]
target_scan = [scan for scan in scan_list if scan not in g_scan]

mstransform(mymms,outmms,createmms=True,datacolumn='corrected',numsubms=len(target_scan),field=target_field)

filename = work_dir+'/config.py'
with open(filename, 'a') as file:
    file.write('FILE_output_ms = "'+outmms+'" \n')