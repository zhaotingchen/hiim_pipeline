#mpicasa, LARGE, config.py, 0
import glob
import sys
import os
import numpy as np

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

bp_scan_field_name = strlist_to_str(CAL_1GC_PRIMARY_NAME)
p_scan_field_name = strlist_to_str(CAL_1GC_SECONDARY_NAME)


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
         clipminmax = [0.0,50.0],
         flagbackup=False,
        )

print('Flag primary calibrator data...')
flagdata(vis=mymms,mode='rflag',datacolumn='data',field=bp_scan_field_name,flagbackup=False,)
flagdata(vis=mymms,mode='tfcrop',datacolumn='data',field=bp_scan_field_name,flagbackup=False,)
flagdata(vis=mymms,mode='extend',growtime=90.0,growfreq=90.0,growaround=True,flagneartime=True,flagnearfreq=True,field=bp_scan_field_name,flagbackup=False,)

print('Flag secondary calibrator data...')
flagdata(vis=mymms,mode='rflag',datacolumn='data',field=p_scan_field_name,flagbackup=False,)
flagdata(vis=mymms,mode='tfcrop',datacolumn='data',field=p_scan_field_name,flagbackup=False,)
flagdata(vis=mymms,mode='extend',growtime=90.0,growfreq=90.0,growaround=True,flagneartime=True,flagnearfreq=True,field=p_scan_field_name,flagbackup=False,)

#print('Adding model column...')
#clearcal(vis = mymms, addmodel = True)



if save_flag:
    print('Saving flags...')
    flagmanager(vis = mymms,
                mode = 'save',
                versionname = 'pre_1GC')
    
clearstat()
clearstat()