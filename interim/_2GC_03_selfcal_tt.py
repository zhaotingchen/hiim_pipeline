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
from hiimtool.ms_tool import get_nscan,get_antnames



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

mymms = FILE_working_ms
gain_dir = OUTPUT_cal
block_id = find_block_id(mymms)
if CAL_1GC_ref_ant != 'auto':
    ref_ant = CAL_1GC_ref_ant
else:
    ref_ant = strlist_to_str(list(CAL_1GC_ref_pool))
    
bpfield_name = strlist_to_str(CAL_1GC_PRIMARY_NAME)
myuvrange = config['CAL_2GC']['uvrange']
temp_dir = OUTPUT_temp

bp_scan = np.sort(unravel_list(CAL_1GC_PRIMARY_SCAN)).tolist()
p_scan = np.sort(unravel_list(CAL_1GC_SECONDARY_SCAN)).tolist()
scan_sort = np.argsort(bp_scan+p_scan)
g_scan = np.sort(bp_scan+p_scan).tolist()
nscan = get_nscan(mymms)
scan_list = ['%04i' % scan for scan in range(nscan)]
target_scan = [scan for scan in scan_list if scan not in g_scan]

target_field = strlist_to_str([field for field in CAL_1GC_FIELD_NAMES if field not in (CAL_1GC_PRIMARY_NAME+CAL_1GC_SECONDARY_NAME)])

if CAL_1GC_ref_ant != 'auto':
    ref_ant = CAL_1GC_ref_ant
else:
    ref_ant = strlist_to_str(list(CAL_1GC_ref_pool))


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


num_scan_prim = [len(x) for x in CAL_1GC_PRIMARY_SCAN]
num_scan_sec = [len(x) for x in CAL_1GC_SECONDARY_SCAN]
bp_scan_field_name = np.repeat(CAL_1GC_PRIMARY_NAME,num_scan_prim).tolist()
p_scan_field_name = np.repeat(CAL_1GC_SECONDARY_NAME,num_scan_sec).tolist()

g_scan_field_name = np.array(bp_scan_field_name+p_scan_field_name)[scan_sort].tolist()
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

bptabc = gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(1)
gtabc = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(1)

caltype='G'
cal_args = {
    'interp':['nearest','linear','linear','linear'],
    'solint':solint,
    'calmode':'p',
}
arglist = []

for i,scan in enumerate(target_scan):
    pair_indx = np.argmin(np.abs(np.array(p_scan).astype('int')-int(scan)))
    pair_scan = p_scan[pair_indx]
    ktabc = gain_dir+'/cal_1GC_'+block_id+'_'+pair_scan+'.'+'K3'
    ftabc = gain_dir+'/cal_1GC_'+block_id+'_'+pair_scan+'.'+'flux3'
    subms = get_subms(scan)
    scan_args = cal_args.copy()
    scan_args['gaintable']=[ktabc,gtabc,bptabc,ftabc]
    scan_args['gainfield'] = ['',strlist_to_str(np.unique(bp_scan_field_name)),strlist_to_str(np.unique(bp_scan_field_name)),p_scan_field_name[pair_indx]]
    scan_args['field'] = target_field
    caltable = gain_dir+'/cal_2GC_'+block_id+'_'+scan+'.'+'G'+str(cround)
    scan_args['caltable'] = caltable
    arglist += [(subms,caltype,cround,scan_args),]
    
for arg in arglist:
    gaincal_worker(arg[0],arg[1],arg[2],arg[3])

gtabc = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(1)
bptabc = gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(1)
app_args = {'interp':['nearest','linear','linear','linear'],
           }

arglist = []
for i,scan in enumerate(target_scan):
    pair_indx = np.argmin(np.abs(np.array(p_scan).astype('int')-int(scan)))
    pair_scan = p_scan[pair_indx]
    gtabself = gain_dir+'/cal_2GC_'+block_id+'_'+scan+'.'+'G'+str(cround)
    ktabc = gain_dir+'/cal_1GC_'+block_id+'_'+pair_scan+'.'+'K'+str(3)
    ftabc = gain_dir+'/cal_1GC_'+block_id+'_'+pair_scan+'.'+'flux'+str(3)
    subms = get_subms(scan)
    scan_args = app_args.copy()
    scan_args['gaintable'] = [ktabc,gtabc,bptabc,ftabc,gtabself]
    scan_args['gainfield'] = ['',strlist_to_str(np.unique(bp_scan_field_name)),strlist_to_str(np.unique(bp_scan_field_name)),p_scan_field_name[pair_indx],target_field]
    scan_args['field'] = target_field
    arglist += [(subms,scan_args['gaintable'],scan_args['gainfield'],scan_args),]
    
for arg in arglist:
    applycal_worker(arg[0],arg[1],arg[2],arg[3])