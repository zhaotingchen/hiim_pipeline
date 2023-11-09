#container, NODE, config.ini, 0
import glob
import sys
import os
import numpy as np
import re
import configparser
from casacore.tables import table as table_alt
from multiprocessing import Pool
from casatools import table


config_file = sys.argv[-1]
config = configparser.ConfigParser()
config.read(config_file)

hiimtool = config['FILE']['hiimtool']
sys.path.append(hiimtool)
from hiimtool.config_util import tidy_config_path
from hiimtool.ms_tool import read_ms,get_nscan,get_antnames


config = tidy_config_path(config)

work_dir = config['FILE']['work_dir']
sys.path.append(work_dir)
from config import *

def get_subms(scan):
    subms = glob.glob(mymms+'/SUBMSS/*'+scan+'*.ms')
    assert len(subms)==1
    return subms[0]

def unravel_list(inp):
    out = [item for sublist in inp for item in sublist]
    return out

mymms = FILE_working_ms
spw_table = table_alt(mymms+'/SPECTRAL_WINDOW',ack=False)
chans = spw_table.getcol('CHAN_FREQ')[0]
temp_dir = OUTPUT_temp
spw_table.close()
p_scan = np.sort(unravel_list(CAL_1GC_SECONDARY_SCAN)).tolist()
bp_scan = np.sort(unravel_list(CAL_1GC_PRIMARY_SCAN)).tolist()

ant_names = get_antnames(mymms)
g_scan = np.sort(p_scan+bp_scan).tolist()
nscan = get_nscan(mymms)

scan_list = ['%04i' % scan for scan in range(nscan)]
target_scan = [scan for scan in scan_list if scan not in g_scan]
pair_indx = np.where((np.array(target_scan).astype('int')[:,None]-np.array(p_scan).astype('int')[None,:])==1)[-1]
target_pair_scan = np.array(p_scan)[pair_indx].tolist()
num_bl = (len(ant_names)*(len(ant_names)+1))//2 # including auto

def flag_dip_worker(scan_indx):
    tscan_i = target_scan[scan_indx]
    pscan_i = target_pair_scan[scan_indx]
    sub_ms = get_subms(pscan_i)
    maintab = table_alt(sub_ms,ack=False)
    ant1= maintab.getcol('ANTENNA1')
    ant2= maintab.getcol('ANTENNA2')
    data = maintab.getcol('CORRECTED_DATA').T
    flag = maintab.getcol('FLAG').T
    data_I = (data[0]+data[-1])/2
    flag_I = (flag[0]+flag[-1])>0
    data_V = (data[0]-data[-1])/2j
    maintab.close()
    data_I = data_I.reshape((len(chans),-1,num_bl))
    data_V = data_V.reshape((len(chans),-1,num_bl))
    flag_I = flag_I.reshape((len(chans),-1,num_bl))
    ant1 = ant1.reshape((-1,num_bl))
    ant2 = ant2.reshape((-1,num_bl))
    flag = flag.reshape((len(flag),len(chans),-1,num_bl))
    V_amp_sq= np.sqrt(np.sum(np.abs(data_V)**2*(1-flag_I),axis=(1,2))/np.sum(1-flag_I,axis=(1,2)))
    ant_flag_dip = np.zeros((len(ant_names),len(chans)),dtype='bool')
    flag_dip = np.zeros_like(flag)
    for ant_sel in range(len(ant_names)):
        sel_indx = ((ant1==ant_sel) + (ant2==ant_sel))>0
        flux_scale_ant = np.sum(data_I*(1-flag_I)*sel_indx[None,:,:],axis=(1,2))/np.sum((1-flag_I)*sel_indx[None,:,:],axis=(1,2))
        sigma_v_err = V_amp_sq/np.sqrt(((1-flag_I)*sel_indx[None,:,:]).sum(axis=(1,2)))
        smooth_ant = gaussian_filter(np.abs(flux_scale_ant),5)
        ant_flag_dip[ant_sel] = (np.abs(flux_scale_ant)<=(smooth_ant-4/np.sqrt(2)*sigma_v_err))
        ant_flag_dip[ant_sel] += (np.abs(flux_scale_ant)>=(smooth_ant+4/np.sqrt(2)*sigma_v_err))
        flag_dip[0][:,sel_indx] += ant_flag_dip[ant_sel][:,None]
        flag_dip[-1][:,sel_indx] += ant_flag_dip[ant_sel][:,None]
    flag_update = (flag+flag_dip)>0
    flag_update = flag_update.reshape((len(flag),len(chans),-1))
    tb = table()
    tb.open(sub_ms,nomodify=False)
    tb.putcol('FLAG',flag_update)
    tb.close()
    #propogate the flag to target scan
    t_scan = target_scan[scan_indx]
    sub_ms = get_subms(t_scan)
    flag,ant1,ant2 = read_ms(sub_ms,['flag','antenna1','antenna2'],verbose=True)
    flag = flag.reshape((len(flag),len(chans),-1,num_bl))
    ant1 = ant1.reshape((-1,num_bl))
    ant2 = ant2.reshape((-1,num_bl))
    flag_dip = np.zeros_like(flag)
    for ant_sel in range(len(ant_names)):
        sel_indx = ((ant1==ant_sel) + (ant2==ant_sel))>0
        flag_dip[0][:,sel_indx] += ant_flag_dip[ant_sel][:,None]
        flag_dip[-1][:,sel_indx] += ant_flag_dip[ant_sel][:,None]
    flag_update = (flag+flag_dip)>0
    flag_update = flag_update.reshape((len(flag),len(chans),-1))
    tb = table()
    tb.open(sub_ms,nomodify=False)
    tb.putcol('FLAG',flag_update)
    tb.close()
    return 1

if __name__ == '__main__':
    with Pool() as p:
        p.map(flag_dip_worker, range(len(target_scan)))