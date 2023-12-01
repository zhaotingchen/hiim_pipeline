#container, BASIC, config.ini, 0
import glob
import sys
import os
import numpy as np
import configparser

jobname = '2GC_02_wsclean_casaselfcal'

config_file = sys.argv[-1]
config = configparser.ConfigParser()
config.read(config_file)

hiimtool = config['FILE']['hiimtool']
sys.path.append(hiimtool)
from hiimtool.config_util import gen_syscall_wsclean,job_handler,tidy_config_path,get_file_setup,find,gen_syscall

config = tidy_config_path(config)

work_dir = config['FILE']['work_dir']
sys.path.append(work_dir)
from config import *


mymms = FILE_working_ms
temp_dir = OUTPUT_temp

def strlist_to_str(inp):
    out = ''
    for vals in inp:
        out += vals+','
    out = out[:-1]
    return out

def unravel_list(inp):
    out = [item for sublist in inp for item in sublist]
    return out

target_field = [field for field in CAL_1GC_FIELD_NAMES if field not in (CAL_1GC_PRIMARY_NAME+CAL_1GC_SECONDARY_NAME)][0]

file_setup = dict(config['WSCLEAN_2GC_00']).copy()
nloop = int(config['CAL_2GC']['nloop'])

field_id = np.where(np.array(CAL_1GC_FIELD_NAMES) == target_field)[0]
file_setup['field'] =strlist_to_str(np.vectorize(str)(field_id))
file_setup['name'] = OUTPUT_image + '/' + target_field+'_tt0'

syscall = gen_syscall_wsclean(mymms,config,file_setup)

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

syscall += cal_syscall[0]+' \n'

for i in range(1,nloop):
    file_setup = dict(config['WSCLEAN_2GC_loop']).copy()
    file_setup['field'] =strlist_to_str(np.vectorize(str)(field_id))
    file_setup['name'] = OUTPUT_image + '/' + target_field+'_tt'+str(i)
    syscall += gen_syscall_wsclean(mymms,config,file_setup)
    syscall += cal_syscall[i]

job_handler(syscall,jobname,config,'WSCLEAN')