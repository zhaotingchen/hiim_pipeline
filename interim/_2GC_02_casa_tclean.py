#containermpi, NODE, config.ini, nloop
import glob
import sys
import os
import numpy as np
import re
from casatasks import *
import configparser

cround = int(sys.argv[-2])

config_file = sys.argv[-1]
config = configparser.ConfigParser()
config.read(config_file)

hiimtool = config['FILE']['hiimtool']
sys.path.append(hiimtool)
from hiimtool.config_util import tidy_config_path
from hiimtool.ms_tool import get_nscan,get_antnames,get_chanfreq
from hiimtool.basic_util import find_block_id

config = tidy_config_path(config)

work_dir = config['FILE']['work_dir']
sys.path.append(work_dir)
from config import *

def strlist_to_str(inp):
    out = ''
    for vals in inp:
        out += vals+','
    out = out[:-1]
    return out

def str_to_strlist_int(inp):
    out = []
    for vals in inp.split(','):
        out+= [int(vals),]
    return out

def unravel_list(inp):
    out = [item for sublist in inp for item in sublist]
    return out

mymms = FILE_output_ms
if cround>0:
    clean_setup = dict(config['TCLEAN_2GC_loop']).copy()
else:
    clean_setup = dict(config['TCLEAN_2GC_00']).copy()

block_id = find_block_id(mymms)
imagename = OUTPUT_image+'/'+block_id+'_2GC_r'+str(cround)
#run tclean
tclean(mymms,imsize=int(clean_setup['size']),
       cell=clean_setup['scale'],
       imagename = imagename,
       specmode='mfs',
       weighting=clean_setup['weighting'],
       robust = float(clean_setup['robust']),
       gridder = 'wproject',
       deconvolver='mtmfs',
       scales=str_to_strlist_int(clean_setup['scales']),
       gain = float(clean_setup['gain']),
       nterms = int(clean_setup['nterms']),
       niter = int(clean_setup['niter']),
       parallel = True,
       savemodel='none',
)

#save model column
tclean(mymms,imsize=int(clean_setup['size']),
       cell=clean_setup['scale'],
       imagename = imagename,
       specmode='mfs',
       weighting=clean_setup['weighting'],
       robust = float(clean_setup['robust']),
       gridder = 'wproject',
       deconvolver='mtmfs',
       scales=str_to_strlist_int(clean_setup['scales']),
       gain = float(clean_setup['gain']),
       nterms = int(clean_setup['nterms']),
       niter = 0,
       parallel = False,
       savemodel='modelcolumn',
)
