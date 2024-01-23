#containermpi, NODE, config.ini, nloop
import glob
import sys
import os
import numpy as np
import re
from casatasks import *
import configparser
import shutil

cround = int(sys.argv[-2])

config_file = sys.argv[-1]
config = configparser.ConfigParser()
config.read(config_file)

hiimtool = config['FILE']['hiimtool']
sys.path.append(hiimtool)
from hiimtool.config_util import tidy_config_path
from hiimtool.ms_tool import get_chanfreq

config = tidy_config_path(config)

work_dir = config['FILE']['work_dir']
sys.path.append(work_dir)
from config import *

def find_block_id(filename):
    reex = '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'
    result = re.findall(reex,filename)
    if result.count(result[0]) != len(result):
        raise ValueError("ambiguous block id from filename "+filename)
    result = result[0]
    return result

def strlist_to_str(inp):
    out = ''
    for vals in inp:
        out += vals+','
    out = out[:-1]
    return out

def unravel_list(inp):
    out = [item for sublist in inp for item in sublist]
    return out

def get_subms(scan):
    subms = glob.glob(mymms+'/SUBMSS/*'+scan+'*.ms')
    assert len(subms)==1
    return subms[0]

mymms = FILE_output_ms
gain_dir = OUTPUT_cal
block_id = find_block_id(mymms)
if CAL_1GC_ref_ant != 'auto':
    ref_ant = CAL_1GC_ref_ant
else:
    ref_ant = strlist_to_str(list(CAL_1GC_ref_pool))
    
myuvrange = config['CAL_2GC']['uvrange']

target_field = strlist_to_str([field for field in CAL_1GC_FIELD_NAMES if field not in (CAL_1GC_PRIMARY_NAME+CAL_1GC_SECONDARY_NAME)])

def gaincal_worker(subms,gaintype,cal_round,update_pars,norun=False):
    cal_pars = gaincal_default.copy()
    cal_pars.update(update_pars)
    if 'caltable' in cal_pars.keys():
        #override the output name
        caltable = cal_pars['caltable']
    else:
        scan = find_scan(subms)
        caltable = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+gaintype+str(cal_round)
    if norun:
        return subms,caltable,cal_pars
    gaincal(vis=subms,
            field=cal_pars['field'],
            uvrange=cal_pars['uvrange'],
            spw=cal_pars['spw'],
            caltable=caltable,
            refant=cal_pars['refant'],
            gaintype=gaintype,
            solint=cal_pars['solint'],
            parang=cal_pars['parang'],
            gaintable=cal_pars['gaintable'], 
            gainfield=cal_pars['gainfield'], 
            interp=cal_pars['interp'],
            calmode=cal_pars['calmode'],
            minsnr=cal_pars['minsnr'],
            minblperant=cal_pars['minblperant'],
            append=cal_pars['append'],
            scan=cal_pars['scan']
           )
    return 1

def applycal_worker(subms,gaintable,gainfield,update_pars,norun=False):
    apply_pars = applycal_default.copy()
    apply_pars.update(update_pars)
    if norun:
        return subms,gaintable,gainfield,apply_pars
    applycal(vis=subms,
             field=apply_pars['field'],
             gaintable=gaintable,
             parang=apply_pars['parang'],
             gainfield=gainfield,
             interp=apply_pars['interp'],
             spw=apply_pars['spw'],
             flagbackup=False,
            )
    return 1

minsnr = float(config['CAL_2GC']['minsnr'])
solint = config['CAL_2GC']['solint']

gaincal_default = {
    'uvrange':myuvrange,
    'spw':'',
    'refant':ref_ant,
    'solint':'inf',
    'parang':False,
    'gaintable':'',
    'gainfield':'',
    'interp':'',
    'minsnr':minsnr,
    'calmode':'p',
    'minblperant':4,
    'append':False,
    'field':'',
    'scan':'',
}

applycal_default = {
    'parang':False,
    'interp':'',
    'field':'',
    'spw':'',
}

num_sub_spw = int(CAL_2GC_phase_sub_band)
num_ch = len(get_chanfreq(mymms))
num_ch_per_i = np.ones(num_sub_spw,dtype='int')*num_ch//num_sub_spw
num_ch_per_i[:num_ch%num_sub_spw]+=1
num_ch_cumu_i = np.cumsum(num_ch_per_i)
num_ch_cumu_i = np.append(0,num_ch_cumu_i)

spw_str = ()
for i in range(num_sub_spw):
    low_indx = num_ch_cumu_i[i]
    up_indx = num_ch_cumu_i[i+1]-1
    spw_i = '*:'+str(low_indx)+'~'+str(up_indx)
    spw_str += (spw_i,)


caltype='G'
cal_args = {
    'solint':solint,
    'calmode':'p',
}
arglist = []
for spw_i in range(num_sub_spw): 
    scan_args = cal_args.copy()
    gtabself = gain_dir+'/cal_2GC_'+block_id+'_subspw_'+str(spw_i)+'.'+caltype+str(cround)
    scan_args['caltable'] = gtabself
    scan_args['spw'] = spw_str[spw_i]
    arglist += [(mymms,caltype,cround,scan_args),]

for arg in arglist:
    gaincal_worker(arg[0],arg[1],arg[2],arg[3])

app_args = {'interp':'nearest',
           }
arglist = []
for spw_i in range(num_sub_spw):
    scan_args = app_args.copy()
    gtabself = gain_dir+'/cal_2GC_'+block_id+'_subspw_'+str(spw_i)+'.'+caltype+str(cround)
    scan_args['gaintable'] = [gtabself,]
    scan_args['spw'] = spw_str[spw_i]
    scan_args['gainfield'] = [target_field,]
    arglist += [(mymms,scan_args['gaintable'],scan_args['gainfield'],scan_args),]
        
for arg in arglist:
    applycal_worker(arg[0],arg[1],arg[2],arg[3])