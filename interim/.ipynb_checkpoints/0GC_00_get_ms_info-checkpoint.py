#container, BASIC, config.ini
import glob
import configparser 
import sys
import os
import re
import json

def find(s, ch):
    return [i for i, ltr in enumerate(s) if ltr == ch]

config_file = sys.argv[1]
config = configparser.ConfigParser()
config.read(config_file)

hiimtool = config['FILE']['hiimtool']
sys.path.append(hiimtool)
from hiimtool.ms_tool import *
from hiimtool.config_util import tidy_config_path,ini_to_json

config = tidy_config_path(config)

master_ms = config['FILE']['master_ms']
nchan = get_nchan(master_ms)

PRE_NCHANS = config['PRE']['NCHANS']

if PRE_NCHANS == '':
    working_ms = master_ms.replace('.ms','_'+str(nchan)+'ch.mms')
else:
    working_ms = master_ms.replace('.ms','_'+str(PRE_NCHANS)+'ch.mms')
    
st_indx = find(working_ms.rstrip('/'),'/')[-1]+1

working_ms = working_ms.rstrip('/')[st_indx:]
working_ms = config['FILE']['work_dir']+'/'+working_ms

config['FILE']['working_ms']=working_ms

with open(config['FILE']['work_dir']+'/config.json','w') as f:
    print('saved config to '+config['FILE']['work_dir']+'/config.json')
    json.dump(ini_to_json(config),f)

