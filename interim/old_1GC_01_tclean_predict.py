#mpipython, LARGE, config.ini, CAL_1GC_PRIMARY_STATE
import glob
import sys
import os
import numpy as np
import configparser
from casatasks import tclean

primary_i = int(sys.argv[-2])
config_file = sys.argv[-1]
config = configparser.ConfigParser()
config.read(config_file)

hiimtool = config['FILE']['hiimtool']
sys.path.append(hiimtool)
from hiimtool.config_util import tidy_config_path

config = tidy_config_path(config)

work_dir = config['FILE']['work_dir']
sys.path.append(work_dir)
from config import *


mymms = FILE_working_ms
save_flag = bool(CAL_1GC_save_flag)
use_field = bool(CAL_1GC_use_field_sources)
data_dir = FILE_interim[:-7]+'data/'

primary_name = CAL_1GC_PRIMARY_NAME[primary_i]

if not use_field:
    raise ValueError('use set_jy instead of this to ignore field sources')

#for primary_i,primary_name in enumerate(CAL_1GC_PRIMARY_NAME):
if ((primary_name != '1934-638')*(primary_name != '0408-65')):
    raise ValueError('Only support primary calibrator 1934-638 or 0408-65 currently')
print('Dirty image for '+primary_name+':')
imname = OUTPUT_image+'/'+primary_name+'_dirty'
tclean(vis=mymms, imagename=imname, 
       scan=CAL_1GC_PRIMARY_SCAN[primary_i][0],
       imsize=2048, cell='12.0arcsec',
       specmode='cube',weighting='natural', niter=0,
      calcpsf=True,parallel=True)
    
#clearstat()
#clearstat()
        