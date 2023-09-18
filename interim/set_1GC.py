'''
Create sbatch scripts to run
'''

import glob
import datetime
import time
import os
import os.path as o
import sys
import configparser

def unravel_list(inp):
    out = [item for sublist in inp for item in sublist]
    return out

config_file = sys.argv[1]
config = configparser.ConfigParser()
config.read(config_file)

hiimtool = config['FILE']['hiimtool']
sys.path.append(hiimtool)

from hiimtool.config_util import gen_syscall,job_handler,tidy_config_path,get_file_setup,find

config = tidy_config_path(config)

work_dir = config['FILE']['work_dir']
sys.path.append(work_dir)
from config import *

pylist = glob.glob(config['FILE']['interim']+'/1GC*')

for file in pylist[:]:
    #print(file)
    file_setup = get_file_setup(file)
    #print(file_setup['loop'])
    if file_setup['loop'].isnumeric():
        loop = int(file_setup['loop'])
    else:
        loop = len(unravel_list(locals()[file_setup['loop']]))
    syscall = gen_syscall(file_setup['calltype'],
                          file,
                          config,
                          args=config['FILE']['work_dir']+'/'+file_setup['args'],
                         loop=loop)
    jobname = file[find(file,'/')[-1]+1:find(file,'.')[-1]]
    job_handler(syscall,jobname,config,file_setup['jobtype'])

