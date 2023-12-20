#container, BASIC, config.ini, 0
import glob
import sys
import os
import numpy as np
import configparser
from astropy.io import fits 
from casacore.tables import table 
import pandas as pd
from astropy.wcs import WCS
from astropy.coordinates import Angle

jobname = '2GC_03_wsclean_casaselfcal'

config_file = sys.argv[-1]
config = configparser.ConfigParser()
config.read(config_file)

hiimtool = config['FILE']['hiimtool']
sys.path.append(hiimtool)
from hiimtool.config_util import gen_syscall_wsclean,job_handler,tidy_config_path,get_file_setup,find,gen_syscall
from hiimtool.ms_tool import get_nchan

config = tidy_config_path(config)

work_dir = config['FILE']['work_dir']
sys.path.append(work_dir)
from config import *

mymms = FILE_working_ms
spw_table = table(mymms+'/SPECTRAL_WINDOW',ack=False)
chans = spw_table.getcol('CHAN_FREQ')[0] 
deltav = np.diff(chans).mean()
target_field = [field for field in CAL_1GC_FIELD_NAMES if field not in (CAL_1GC_PRIMARY_NAME+CAL_1GC_SECONDARY_NAME)][0]

def strlist_to_str(inp):
    out = ''
    for vals in inp:
        out += vals+','
    out = out[:-1]
    return out

def unravel_list(inp):
    out = [item for sublist in inp for item in sublist]
    return out

file_setup = dict(config['WSCLEAN_2GC_00']).copy()
nloop = int(config['CAL_2GC']['nloop'])

field_id = np.where(np.array(CAL_1GC_FIELD_NAMES) == target_field)[0]
file_setup['field'] =strlist_to_str(np.vectorize(str)(field_id))
file_setup['name'] = OUTPUT_image + '/' + target_field+'_r0'

syscall = gen_syscall_wsclean(mymms,config,file_setup)

file = config['FILE']['interim']+'/_2GC_02_write_empty_im.py'
python_setup = get_file_setup(file)

prep_syscall = gen_syscall(python_setup['calltype'],
                          file,
                          config,
                          jobtype=python_setup['jobtype'],
                          args=config['FILE']['work_dir']+'/'+python_setup['args'],)

syscall += prep_syscall+' \n'

file = config['FILE']['interim']+'/_2GC_03_selfcal_tt.py'
python_setup = get_file_setup(file)
python_script = config['FILE']['interim']+'/_2GC_03_selfcal_tt.py'
cal_syscall = gen_syscall(python_setup['calltype'],
                          file,
                          config,
                          jobtype=python_setup['jobtype'],
                          args=config['FILE']['work_dir']+'/'+python_setup['args'],
                         loop=nloop)
cal_syscall = cal_syscall.split('\n')

restore_setup = dict()
restore_setup['temp-dir'] = file_setup['temp-dir']
if 'verbose' in file_setup.keys():
    restore_setup['verbose'] = ''
restore_setup['restore-list'] = ''
    
predict_setup = dict()
predict_setup['temp-dir'] = file_setup['temp-dir']
if 'verbose' in file_setup.keys():
    predict_setup['verbose'] = ''
predict_setup['name'] = '{OUTPUT_temp}/{target_field}_predict'.format(**locals())
predict_setup['field'] = strlist_to_str(np.vectorize(str)(field_id))
predict_setup['channels-out'] = str(len(chans))
predict_setup['predict'] = ''

syscall_predict = gen_syscall_wsclean(mymms,config,predict_setup)

for cround in range(nloop):
    if cround == 0:
        syscall_im = ''
    else:
        file_setup = dict(config['WSCLEAN_2GC_loop']).copy()
        file_setup['field'] =strlist_to_str(np.vectorize(str)(field_id))
        file_setup['name'] = OUTPUT_image + '/' + target_field+'_r'+str(cround)
        syscall_im = gen_syscall_wsclean(mymms,config,file_setup)
        
    source_list = '{OUTPUT_image}/{target_field}_r'.format(**locals())+str(cround)+'-sources.txt'
    syscall_restore = ''
    for i in range(len(chans)):
        predict_in = ('{OUTPUT_temp}/{target_field}_predict-%04i-residual.fits' %i).format(**locals())
        predict_out = ('{OUTPUT_temp}/{target_field}_predict-%04i-model.fits' %i).format(**locals())
        syscall_restore += gen_syscall_wsclean(predict_in+' '+source_list+' '+predict_out,
                                               config,restore_setup)
    syscall_rm = ('rm {OUTPUT_temp}/{target_field}_predict-*-model.fits \n').format(**locals())
    syscall += (syscall_im+syscall_restore+syscall_predict+cal_syscall[2*cround]+'\n'+cal_syscall[2*cround+1]+'\n'+syscall_rm)
syscall_rm = ('rm {OUTPUT_temp}/{target_field}_predict-*-residual.fits \n').format(**locals())
syscall += syscall_rm

#find possible multiple module load
syscall_tidy = ''
module_list = ()
for sys_line in syscall.split('\n'):
    if sys_line[:11] == 'module load':
        module_list+= (sys_line,)
    else:
        syscall_tidy += sys_line+'\n'
        
module_list = np.unique(np.array(module_list))

syscall_module = ''
for module in module_list:
    syscall_module += module+'\n'
    
job_handler(syscall_module+syscall_tidy,jobname,config,'WSCLEAN')