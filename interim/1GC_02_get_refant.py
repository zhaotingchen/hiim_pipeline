#container, BASIC, config.ini, 0
import glob
import sys
import os
import numpy as np
import configparser

config_file = sys.argv[-1]
config = configparser.ConfigParser()
config.read(config_file)

hiimtool = config['FILE']['hiimtool']
sys.path.append(hiimtool)
from hiimtool.config_util import tidy_config_path
from hiimtool.ms_tool import read_ms,get_antnames

config = tidy_config_path(config)

work_dir = config['FILE']['work_dir']
sys.path.append(work_dir)
from config import *


mymms = FILE_working_ms


def get_ref_ant():
    if CAL_1GC_ref_ant != 'auto':
        return CAL_1GC_ref_ant
    antnames = get_antnames(mymms)
    ant_indx = np.arange(len(antnames))
    ant_bl_count = np.zeros(len(antnames))
    ant_flag_count = np.zeros(len(antnames))
    scan_list = [scan for sublist in CAL_1GC_PRIMARY_SCAN for scan in sublist]
    for scan in scan_list:
        subms = glob.glob(mymms+'/SUBMSS/*'+scan+'*.ms')[0]
        flag,ant1,ant2 = read_ms(subms,
                                 ['flag','antenna1','antenna2'],
                                 verbose=False)
        sel_indx = ((ant1[:,None] == ant_indx[None,:])+(ant2[:,None] == ant_indx[None,:]))>0
        # don't count auto-corr
        cross_corr = (sel_indx.sum(axis=-1)>1)
        flag = flag[:,:,cross_corr]
        sel_indx = sel_indx[cross_corr,:]
        flag = flag.mean(axis=(0,1))
        # add counts
        ant_bl_count += sel_indx.sum(axis=0)
        ant_flag_count += (flag[:,None]*sel_indx).sum(axis=0)
    for i,ant in enumerate(antnames):
        print('Antenna '+ant+' is %.4f percent flagged' % (ant_flag_count/ant_bl_count*100)[i])
    
    ref_ant = np.array(antnames)[np.argsort(ant_flag_count/ant_bl_count)].tolist()
    return ref_ant

ref_ant = get_ref_ant()
with open(FILE_work_dir+'/config.py','a') as f:
    f.write('\nCAL_1GC_ref_pool = '+ str(ref_ant))




        