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

from hiimtool.config_util import tidy_config_path,ini_to_py

config = tidy_config_path(config)

ini_to_py(config,config['FILE']['work_dir']+'/config.py',append=True)