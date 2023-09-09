#mpicasa, LARGE, config.py, 0
import glob
import sys
import os
import numpy as np

config_file = sys.argv[-1]
execfile(config_file)
mymms = FILE_working_ms
save_flag = bool(CAL_1GC_save_flag)
use_field = bool(CAL_1GC_use_field_sources)
data_dir = FILE_interim[:-7]+'data/'

if use_field:
    raise ValueError('Set_Jy does not use field sources')

for primary_name in CAL_1GC_PRIMARY_NAME:
    print('Populating Model for '+primary_name)
    if ((primary_name != '1934-638')*(primary_name != '0408-65')):
        raise ValueError('Only support 1934-638 or 0408-65 currently')
        field_id = np.where(np.array(CAL_1GC_FIELD_NAMES) == primary_name)[0][0]
        #cl_data = cl()
        cl.done()
    cl.open(data_dir+primary_name+'.cl')
    if use_field is not True:
        #cl_work = cl()
        cl.concatenate(cl.torecord(), [0])
    ft(mymms,field=str(field_id),complist=cl,usescratch=True)
    cl.done()
    
    