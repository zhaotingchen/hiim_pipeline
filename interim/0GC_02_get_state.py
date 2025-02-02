#container, BASIC, config.ini, 0
import sys
import configparser 
from casacore.tables import table
import re
import json
import glob
import numpy as np

config_file = sys.argv[-1]
config = configparser.ConfigParser()
config.read(config_file)
hiimtool = config['FILE']['hiimtool']
sys.path.append(hiimtool)
from hiimtool.config_util import tidy_config_path
config = tidy_config_path(config)


config_path = config['FILE']['work_dir']
sys.path.append(config_path)
from config import FILE_working_ms,FILE_hiimtool,CAL_1GC_primary_intent,CAL_1GC_secondary_intent,CAL_1GC_target_intent
try:
    from config import CAL_1G_polarization_intent
    has_pol_cal = True
except:
    has_pol_cal = False


from hiimtool.ms_tool import get_nchan,get_nscan,get_fields,get_states
from hiimtool.ms_tool import get_primary_candidates,get_secondaries,get_targets,get_primary_tag,get_polarizations
from hiimtool.basic_util import vfind_scan,unravel_list

ms_dir = FILE_working_ms

if has_pol_cal:
    primary_state, secondary_state, target_state, unknown_state,pol_state =get_states(
        ms_dir,
        CAL_1GC_primary_intent,
        CAL_1GC_secondary_intent,
        CAL_1GC_target_intent,
        CAL_1G_polarization_intent
    )
else:
    primary_state, secondary_state, target_state, unknown_state =get_states(
        ms_dir,
        CAL_1GC_primary_intent,
        CAL_1GC_secondary_intent,
        CAL_1GC_target_intent,
    )
    
field_dirs,field_names,field_ids = get_fields(ms_dir)

candidate_dirs, candidate_names, candidate_ids = get_primary_candidates(
    ms_dir,primary_state,unknown_state,field_dirs,field_names,field_ids
)

primary_name,primary_id,primary_tag,primary_sep = get_primary_tag(candidate_dirs,
                candidate_names,
                candidate_ids)

secondary_dirs, secondary_names, secondary_ids = get_secondaries(ms_dir,secondary_state,field_dirs,field_names,field_ids)


target_dirs, target_names, target_ids = get_targets(ms_dir,target_state,field_dirs,field_names,field_ids)

if has_pol_cal:
    pol_dirs, pol_names, pol_ids = get_polarizations(ms_dir,pol_state,field_dirs,field_names,field_ids)
else:
    pol_names = []

dorephrase = (np.array(primary_sep)>1e-5).tolist()

subms_list = np.array(glob.glob(ms_dir+'/SUBMSS/*.ms'))
scan_list = vfind_scan(subms_list)
sort_indx = np.argsort(scan_list)
scan_list = scan_list[sort_indx]
subms_list = subms_list[sort_indx]

primary_scan = []
for i in range(len(primary_state)):
    primary_scan += [[],]

secondary_scan = []
for i in range(len(secondary_state)):
    secondary_scan += [[],]

pol_scan = []
if has_pol_cal:
    for i in range(len(pol_state)):
        pol_scan += [[],]

target_scan = []

for i,scan_id in enumerate(scan_list):
    sub_ms = subms_list[i]
    tab = table(sub_ms,ack=False)
    sub_state = np.unique(tab.getcol('STATE_ID'))
    if sub_state in primary_state:
        primary_scan[primary_state.index(sub_state)] += (scan_id,)
    if sub_state in secondary_state:
        secondary_scan[secondary_state.index(sub_state)] += (scan_id,)
    if has_pol_cal:
        if sub_state in pol_state:
            pol_scan[pol_state.index(sub_state)] += (scan_id,)
    if sub_state in target_state:
        target_scan+= (scan_id,)


with open('config.py','a') as file:
    file.write('CAL_1GC_PRIMARY_STATE'+' = '+str(primary_state)+'\n')
    file.write('CAL_1GC_SECONDARY_STATE'+' = '+str(secondary_state)+'\n')
    file.write('CAL_1GC_TARGET_STATE'+' = '+str(target_state)+'\n')
    file.write('CAL_1GC_UNKNOWN_STATE'+' = '+str(unknown_state)+'\n')
    file.write('CAL_1GC_FIELD_NAMES'+' = '+str(field_names)+'\n')
    file.write('CAL_1GC_PRIMARY_NAME'+' = '+str(primary_name)+'\n')
    file.write('CAL_1GC_SECONDARY_NAME'+' = '+str(secondary_names)+'\n')
    file.write('CAL_1GC_REPHASE'+' = '+str(dorephrase)+'\n')
    file.write('CAL_1GC_PRIMARY_SCAN'+' = '+str(primary_scan)+'\n')
    file.write('CAL_1GC_SECONDARY_SCAN'+' = '+str(secondary_scan)+'\n')
    file.write('CAL_1GC_TARGET_NAME'+' = '+str(target_names)+'\n')
    file.write('CAL_1GC_TARGET_SCAN'+' = '+str(target_scan)+'\n')
    if has_pol_cal:
        file.write('CAL_1GC_POL_SCAN'+' = '+str(pol_scan)+'\n')
        file.write('CAL_1GC_POL_NAME'+' = '+str(pol_names)+'\n')
        file.write('CAL_1GC_POL_STATE'+' = '+str(pol_state)+'\n')
