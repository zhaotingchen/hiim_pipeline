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
from hiimtool.config_util import tidy_config_path

config = tidy_config_path(config)

for path in (config['FILE']['log'],config['FILE']['script']):
    if os.path.isdir(path): continue
    os.mkdir(path)
        