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

print('Adding model column...')
clearcal(vis = mymms, addmodel = True)

if save_flag:
    print('Saving flags...')
    flagmanager(vis = mymms,
                mode = 'save',
                versionname = 'basic')
    
clearstat()
clearstat()