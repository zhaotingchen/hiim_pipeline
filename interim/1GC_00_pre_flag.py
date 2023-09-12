#mpicasa, LARGE, config.py, 0
import glob
import sys
import os
import numpy as np

config_file = sys.argv[-1]
execfile(config_file)
mymms = FILE_working_ms
save_flag = (CAL_1GC_save_flag.lower()=='true')

for REPHASE in CAL_1GC_REPHASE:
    if REPHASE:
        raise ValueError('Field Dir not matching the primary calibrator position')

        
# ------------------------------------------------------------------------
# Frequency ranges to flag over short baselines
if CAL_1GC_bl_spw!='':
    spw_bl = '*:'
    for spw in CAL_1GC_bl_spw.split(','):
        spw_bl += spw.split(':')[-1]+';'
    spw_bl = spw_bl[:-1]
    field_name = ''
    for field in CAL_1GC_PRIMARY_NAME:
        field_name += field+','
    field_name = field_name[:-1]
    flagdata(vis = mymms,
		mode = 'manual', 
        field = field_name,
		spw = spw_bl,
        flagbackup=False,
		uvrange = '0~600m'
            )

print('Flagging autocorr...')
#flag autocorr
flagdata(vis = mymms,
         mode = 'manual',
         autocorr = True,
         flagbackup=False
        )

print('Clipping zeros...')
#clip zeros
flagdata(vis = mymms,
         mode = 'clip',
         clipzeros = True,
         flagbackup=False,
        )

print('Clipping outliers...')
flagdata(vis = mymms,
         mode = 'clip',
         clipminmax = [0.0,100.0],
         flagbackup=False,
        )

#print('Adding model column...')
#clearcal(vis = mymms, addmodel = True)

if save_flag:
    print('Saving flags...')
    flagmanager(vis = mymms,
                mode = 'save',
                versionname = 'pre_1GC')
    
clearstat()
clearstat()