#container, BASIC, config.ini, 0
import glob
import sys
import os
import numpy as np
import configparser
jobname = '2GC_02_casaselfcal'

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

nloop = int(config['CAL_2GC']['nloop'])

tclean_file = config['FILE']['interim']+'/_2GC_02_casa_tclean.py'
tclean_setup = get_file_setup(tclean_file)
tclean_syscall = gen_syscall(
    tclean_setup['calltype'],
    tclean_file,
    config,
    jobtype=tclean_setup['jobtype'],
    args=config['FILE']['work_dir']+'/'+tclean_setup['args'],
    loop=nloop,
)
tclean_syscall = tclean_syscall.split('\n')

cal_file = config['FILE']['interim']+'/_2GC_02_casa_selfcal.py'
cal_setup = get_file_setup(cal_file)
cal_syscall = gen_syscall(
    cal_setup['calltype'],
    cal_file,
    config,
    jobtype=cal_setup['jobtype'],
    args=config['FILE']['work_dir']+'/'+cal_setup['args'],
    loop=nloop,
)
cal_syscall = cal_syscall.split('\n')

syscall_tot = ''
for i in range(len(cal_syscall)):
    syscall_tot += tclean_syscall[i]+'\n'
    syscall_tot += cal_syscall[i]+'\n'
#find possible multiple module load
syscall_tidy = ''
module_list = ()
for sys_line in syscall_tot.split('\n'):
    if sys_line[:11] == 'module load':
        module_list+= (sys_line,)
    else:
        syscall_tidy += sys_line+'\n'
module_list = np.unique(np.array(module_list))
syscall_module = ''
for module in module_list:
    syscall_module += module+'\n'

job_handler(syscall_module+syscall_tidy,jobname,config,tclean_setup['jobtype'])