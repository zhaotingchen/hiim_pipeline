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

config_file = sys.argv[1]
config = configparser.ConfigParser()
config.read(config_file)

hiimtool = config['FILE']['hiimtool']
sys.path.append(hiimtool)

from hiimtool.config_util import gen_syscall,job_handler,tidy_config_path,get_file_setup,find

config = tidy_config_path(config)

pylist = glob.glob(config['FILE']['interim']+'/0GC*')

for file in pylist[:]:
    file_setup = get_file_setup(file)
    syscall = gen_syscall(file_setup['calltype'],
                          file,
                          config,
                          args=config['FILE']['work_dir']+'/'+file_setup['args'])
    jobname = file[find(file,'/')[-1]+1:find(file,'.')[-1]]
    job_handler(syscall,jobname,config,file_setup['jobtype'])

