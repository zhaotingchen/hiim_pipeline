#container, NODE, config.ini, 0
import glob
import sys
import os
import numpy as np
import re
from casatasks import *
import configparser
import shutil

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
save_flag = (CAL_1GC_save_flag.lower()=='true')
gain_dir = OUTPUT_cal
block_id = find_block_id(mymms)
if CAL_1GC_ref_ant != 'auto':
    ref_ant = CAL_1GC_ref_ant
else:
    ref_ant = strlist_to_str(list(CAL_1GC_ref_pool))
    
bpfield_name = strlist_to_str(CAL_1GC_PRIMARY_NAME)
myuvrange = CAL_1GC_uvrange

fillgaps = int(CAL_1GC_fillgaps)
temp_dir = OUTPUT_temp

bp_scan = np.sort(unravel_list(CAL_1GC_PRIMARY_SCAN)).tolist()
p_scan = np.sort(unravel_list(CAL_1GC_SECONDARY_SCAN)).tolist()
scan_sort = np.argsort(bp_scan+p_scan)
g_scan = np.sort(bp_scan+p_scan).tolist()

num_scan_prim = [len(x) for x in CAL_1GC_PRIMARY_SCAN]
num_scan_sec = [len(x) for x in CAL_1GC_SECONDARY_SCAN]

bp_scan_field_name = np.repeat(CAL_1GC_PRIMARY_NAME,num_scan_prim).tolist()
p_scan_field_name = np.repeat(CAL_1GC_SECONDARY_NAME,num_scan_sec).tolist()

g_scan_field_name = np.array(bp_scan_field_name+p_scan_field_name)[scan_sort].tolist()

gaincal_default = {
    'uvrange':myuvrange,
    'spw':'',
    'refant':ref_ant,
    'solint':'inf',
    'parang':False,
    'gaintable':'',
    'gainfield':'',
    'interp':'',
    'minsnr':5,
    'calmode':'ap',
    'minblperant':4,
    'append':False,
    'field':'',
    'scan':'',
}
bandpass_default = {
    'uvrange':myuvrange,
    'spw':'',
    'refant':ref_ant,
    'solint':'inf',
    'parang':False,
    'gaintable':'',
    'gainfield':'',
    'interp':'',
    'minsnr':3.0,
    'solnorm':False,
    'combine':'',
    'minblperant':4,
    'fillgaps':fillgaps,
    'field':'',
}
applycal_default = {
    'parang':False,
    'interp':'',
    'field':'',
}

flagdata_default={
    'field':''
}
fluxscale_default = {'scan':''}

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

def bandpass_worker(subms,bandtype,cal_round,update_pars,norun=False):
    cal_pars = bandpass_default.copy()
    cal_pars.update(update_pars)
    if 'caltable' in cal_pars.keys():
        #override the output name
        caltable = cal_pars['caltable']
    else:
        scan = find_scan(subms)
        caltable = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+gaintype+str(cal_round)
    if norun:
        return subms,caltable,cal_pars
    bandpass(vis=subms,
             field=cal_pars['field'],
             uvrange=cal_pars['uvrange'],
             spw=cal_pars['spw'],
             caltable=caltable,
             refant=cal_pars['refant'],
             solint=cal_pars['solint'],
             combine=cal_pars['combine'],
             minblperant=cal_pars['minblperant'],
             minsnr=cal_pars['minsnr'],
             bandtype=bandtype,
             fillgaps=cal_pars['fillgaps'],
             parang=cal_pars['parang'],
             gaintable=cal_pars['gaintable'], 
             gainfield=cal_pars['gainfield'], 
             interp=cal_pars['interp'],
            )
    return 1

def flagdata_worker(vis,mode,datacolumn,update_pars={}):
    flag_pars = flagdata_default.copy()
    flag_pars.update(update_pars)
    flagdata(vis=vis,mode=mode,datacolumn=datacolumn,
             flagbackup=False,field=flag_pars['field'])
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
             flagbackup=False,
            )
    return 1

def fluxscale_worker(subms,cal_round,update_pars,norun=False):
    cal_pars = fluxscale_default.copy()
    cal_pars.update(update_pars)
    if 'fluxtable' in cal_pars.keys():
        fluxtable = cal_pars['fluxtable']
    else:
        scan = find_scan(subms)
        fluxtable = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'flux'+str(cal_round)
    if norun:
        return subms,fluxtable,cal_pars
    fluxscale(vis=subms,
              caltable=cal_pars['caltable'],
              fluxtable=fluxtable,
              reference=cal_pars['reference'],
              transfer=cal_pars['transfer'],
              scan=cal_pars['scan'],
             )
    return 1

#----------------Flag unfilled model in primary------------------
for scan in bp_scan:
    sub_ms = get_subms(scan)
    flagdata(vis = sub_ms,
         mode = 'clip',
         flagbackup=False,
         correlation='ABS_I',
         clipminmax = [1.01,50.0],
         datacolumn='model',
        )

#----------------Round 0------------------
# Round 0
cround = 0

# Round 0, delay on primary
caltype='K'
#num_proc = len(bp_scan)

cal_args = {'uvrange':'',
            'field':strlist_to_str(np.unique(bp_scan_field_name)),
            'caltable':gain_dir+'/cal_1GC_'+block_id+'.'+caltype+str(cround)
           }
arg = (mymms,caltype,cround,cal_args)
gaincal_worker(arg[0],arg[1],arg[2],arg[3])

# round 0, gain on primary
caltype='G'
#num_proc = len(bp_scan)

cal_args = {'calmode':'p',
            'minsnr':5,
            'interp':['nearest'],
            'field':strlist_to_str(np.unique(bp_scan_field_name)),
            'caltable':gain_dir+'/cal_1GC_'+block_id+'.'+caltype+str(cround),
            'gaintable':gain_dir+'/cal_1GC_'+block_id+'.'+'K'+str(cround),
            'gainfield':strlist_to_str(np.unique(bp_scan_field_name)),
           }
arg = (mymms,caltype,cround,cal_args)
gaincal_worker(arg[0],arg[1],arg[2],arg[3])

#round 0, bandpass on primary
caltype='B'
#num_proc = len(bp_scan)

ktabc = gain_dir+'/cal_1GC_'+block_id+'.'+'K'+str(cround)
gtabc = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(cround)
cal_args = {
            'interp':['nearest','nearest'],
            'gaintable':[ktabc,gtabc],
            'gainfield':[strlist_to_str(np.unique(bp_scan_field_name)),
                         strlist_to_str(np.unique(bp_scan_field_name))],
            'field':strlist_to_str(np.unique(bp_scan_field_name)),
            'caltable':gain_dir+'/cal_1GC_'+block_id+'.'+caltype+str(cround),
           }

arg = (mymms,caltype,cround,cal_args)
bandpass_worker(arg[0],arg[1],arg[2],arg[3])

# flag the bandpass solution
datacol = 'CPARAM'
fmode = 'tfcrop'
arg = (gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(cround),fmode,datacol)
flagdata_worker(arg[0],arg[1],arg[2])

datacol = 'CPARAM'
fmode = 'rflag'
arg = (gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(cround),fmode,datacol)
flagdata_worker(arg[0],arg[1],arg[2])

# apply the solutions to the primary data
ktabc = gain_dir+'/cal_1GC_'+block_id+'.'+'K'+str(cround)
gtabc = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(cround)
btabc = gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(cround)
app_args = {'interp':['nearest','nearest','nearest'],
            'gaintable':[ktabc,gtabc,btabc],
            'gainfield':[strlist_to_str(np.unique(bp_scan_field_name)),
                         strlist_to_str(np.unique(bp_scan_field_name)),
                         strlist_to_str(np.unique(bp_scan_field_name)),],
            'field':strlist_to_str(np.unique(bp_scan_field_name)),
           }

arglist = []
for i,scan in enumerate(bp_scan):
    subms = get_subms(scan)
    arglist += [(subms,app_args['gaintable'],app_args['gainfield'],app_args),]

for arg in arglist:
    applycal_worker(arg[0],arg[1],arg[2],arg[3])

#flag the vis data in prim scans
datacol = 'residual'
fmode = 'rflag'
arglist = []
for i,scan in enumerate(bp_scan):
    subms = get_subms(scan)
    arglist += [(subms,fmode,datacol),]
for arg in arglist:
    flagdata_worker(arg[0],arg[1],arg[2])
    
datacol = 'residual'
fmode = 'tfcrop'
arglist = []
for i,scan in enumerate(bp_scan):
    subms = get_subms(scan)
    arglist += [(subms,fmode,datacol),]
for arg in arglist:
    flagdata_worker(arg[0],arg[1],arg[2])
    
#----------------Round 1------------------
# Round 1
cround = 1

#Round 1, delay on prim
caltype='K'
#num_proc = len(bp_scan)
btab0 = gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(cround-1) 
gtab0 = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(cround-1) 


cal_args = {'uvrange':'',
            'interp':['nearest','nearest'],
            'field':strlist_to_str(np.unique(bp_scan_field_name)),
            'caltable':gain_dir+'/cal_1GC_'+block_id+'.'+caltype+str(cround),
            'gaintable':[gtab0,btab0],
            'gainfield':[strlist_to_str(np.unique(bp_scan_field_name)),
                         strlist_to_str(np.unique(bp_scan_field_name)),]
           }

arg = (mymms,caltype,cround,cal_args)
gaincal_worker(arg[0],arg[1],arg[2],arg[3])

#Round 1, phase on prim
caltype='G'
#num_proc = len(bp_scan)
ktabc = gain_dir+'/cal_1GC_'+block_id+'.'+'K'+str(cround)
btabc = gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(cround-1)
cal_args = {'calmode':'p',
            'minsnr':5,
            'interp':['nearest','nearest'],
            'field':strlist_to_str(np.unique(bp_scan_field_name)),
            'caltable':gain_dir+'/cal_1GC_'+block_id+'.'+caltype+str(cround),
            'gaintable':[ktabc,btabc],
            'gainfield':[strlist_to_str(np.unique(bp_scan_field_name)),
                         strlist_to_str(np.unique(bp_scan_field_name)),],
           }

arg = (mymms,caltype,cround,cal_args)

gaincal_worker(arg[0],arg[1],arg[2],arg[3])


#round 1, bandpass
caltype='B'
#num_proc = len(bp_scan)

ktabc = gain_dir+'/cal_1GC_'+block_id+'.'+'K'+str(cround)
gtabc = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(cround)

cal_args = {
            'interp':['nearest','nearest'],
            'gaintable':[ktabc,gtabc],
            'gainfield':[strlist_to_str(np.unique(bp_scan_field_name)),
                         strlist_to_str(np.unique(bp_scan_field_name))],
            'field':strlist_to_str(np.unique(bp_scan_field_name)),
            'caltable':gain_dir+'/cal_1GC_'+block_id+'.'+caltype+str(cround),
           }
arglist = []
arg = (mymms,caltype,cround,cal_args)

bandpass_worker(arg[0],arg[1],arg[2],arg[3])

#round 1, flag the bandpass solution
datacol = 'CPARAM'
fmode = 'tfcrop'
arg = (gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(cround),fmode,datacol)
flagdata_worker(arg[0],arg[1],arg[2])
                                  
datacol = 'CPARAM'
fmode = 'rflag'
arg = (gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(cround),fmode,datacol)
flagdata_worker(arg[0],arg[1],arg[2])


#Round 1, apply the solutions to the primary data
ktabc = gain_dir+'/cal_1GC_'+block_id+'.'+'K'+str(cround)
gtabc = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(cround)
btabc = gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(cround)
app_args = {'interp':['nearest','nearest','nearest'],
            'gaintable':[ktabc,gtabc,btabc],
            'gainfield':[strlist_to_str(np.unique(bp_scan_field_name)),
                         strlist_to_str(np.unique(bp_scan_field_name)),
                         strlist_to_str(np.unique(bp_scan_field_name)),],
            'field':strlist_to_str(np.unique(bp_scan_field_name)),
           }
arg = (mymms,app_args['gaintable'],app_args['gainfield'],app_args)
applycal_worker(arg[0],arg[1],arg[2],arg[3])

#flag the vis data in prim scans
datacol = 'residual'
fmode = 'rflag'
arglist = []
for i,scan in enumerate(bp_scan):
    subms = get_subms(scan)
    arglist += [(subms,fmode,datacol),]
for arg in arglist:
    flagdata_worker(arg[0],arg[1],arg[2])
    
datacol = 'residual'
fmode = 'tfcrop'
arglist = []
for i,scan in enumerate(bp_scan):
    subms = get_subms(scan)
    arglist += [(subms,fmode,datacol),]
for arg in arglist:
    flagdata_worker(arg[0],arg[1],arg[2])
    
#----------------Round 2------------------
# Round 2
cround = 2
#Round 2 gaincal on primary
caltype='G'
bptabc = gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(cround-1)
gtabc = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(cround-1)
ktabc = gain_dir+'/cal_1GC_'+block_id+'.'+'K'+str(cround-1)

cal_args = {'calmode':'ap',
            'minsnr':3,
            'interp':['nearest','nearest','nearest'],
            'gaintable':[ktabc,gtabc,bptabc],
            'gainfield':[strlist_to_str(np.unique(bp_scan_field_name)),
                         strlist_to_str(np.unique(bp_scan_field_name)),
                         strlist_to_str(np.unique(bp_scan_field_name)),],
            'field':strlist_to_str(np.unique(bp_scan_field_name).tolist()),
            'caltable':gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(cround),
           }
arg =  (mymms,caltype,cround,cal_args)
gaincal_worker(arg[0],arg[1],arg[2],arg[3])

#copy the solutions to each secondary scan
for i,scan in enumerate(p_scan):
    caltable = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'G'+str(cround)
    primtable = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(cround)
    shutil.copytree(primtable,caltable)
    
#Round 2, gain on secondary
caltype='G'
#num_proc = min(len(p_scan),max_num_core)

cal_args = {'calmode':'ap',
            'minsnr':3,
            'interp':('nearest','linear','linear'),
            'gaintable':[ktabc,gtabc,bptabc],
            'gainfield':[strlist_to_str(np.unique(bp_scan_field_name)),
                         strlist_to_str(np.unique(bp_scan_field_name)),
                         strlist_to_str(np.unique(bp_scan_field_name)),],
            'append':True,
           }
arglist = []
for i,scan in enumerate(p_scan):
    caltable = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'G'+str(cround)
    scan_args = cal_args.copy()
    scanlist = strlist_to_str(np.sort(np.array(bp_scan+[scan],dtype='int')+1).astype('str').tolist())
    scan_args['scan'] = scanlist
    scan_args['field'] = p_scan_field_name[i]
    scan_args['caltable'] = caltable
    arglist += [(mymms,caltype,cround,scan_args),]

for arg in arglist:
    gaincal_worker(arg[0],arg[1],arg[2],arg[3])
    
#copy delay tables to each secondary scan
for i,scan in enumerate(p_scan):
    caltable = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'K'+str(cround)
    primtable = gain_dir+'/cal_1GC_'+block_id+'.'+'K'+str(cround-1)
    shutil.copytree(primtable,caltable)
    
#Round 2, delay on secondary
caltype='K'
#num_proc = min(len(p_scan),max_num_core)

cal_args = {
            'interp':('nearest','linear','linear'),
            'append':True,
           }

arglist = []
for i,scan in enumerate(p_scan):
    scan_args = cal_args.copy()
    gtabscan = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'G'+str(cround)
    scanlist = strlist_to_str(np.sort(np.array(bp_scan+[scan],dtype='int')+1).astype('str').tolist())
    scan_args['scan'] = scanlist
    scan_args['field'] = p_scan_field_name[i]
    scan_args['gaintable']=(gtabc,bptabc,gtabscan)
    scan_args['gainfield']=(strlist_to_str(np.unique(bp_scan_field_name)),strlist_to_str(np.unique(bp_scan_field_name)),p_scan_field_name[i])
    scan_args['field'] = p_scan_field_name[i]
    scan_args['caltable'] = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+caltype+str(cround)
    arglist += [(mymms,caltype,cround,scan_args),]
    
for arg in arglist:
    gaincal_worker(arg[0],arg[1],arg[2],arg[3])

#Round 2, flux scale on sec
caltype='flux'
#num_proc = min(len(p_scan),max_num_core)

cal_args = {
    #'reference':np.unique(bp_scan_field_name).tolist()[0]
    
    'reference':strlist_to_str(np.unique(bp_scan_field_name).tolist())
           }

arglist = []
for i,scan in enumerate(p_scan):
    scan_args = cal_args.copy()
    scanlist = strlist_to_str(np.sort(np.array(bp_scan+[scan],dtype='int')+1).astype('str').tolist())
    scan_args['scan'] = scanlist
    scan_args['caltable']=gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'G'+str(cround)
    scan_args['transfer']=p_scan_field_name[i]
    scan_args['fluxtable']=gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'flux'+str(cround)
    arglist+=[(mymms,cround,scan_args),]
    
for i,arg in enumerate(arglist):
    fluxscale_worker(arg[0],arg[1],arg[2])

# apply the solutions to the secondary data
gtabc = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(cround-1)
bptabc = gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(cround-1)
app_args = {'interp':['nearest','linear','linear','linear'],
           }

arglist = []
for i,scan in enumerate(p_scan):
    ktabc = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'K'+str(cround)
    ftabc = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'flux'+str(cround)
    subms = get_subms(scan)
    scan_args = app_args.copy()
    scan_args['gaintable'] = [ktabc,gtabc,bptabc,ftabc]
    scan_args['gainfield'] = ['','',strlist_to_str(np.unique(bp_scan_field_name)),p_scan_field_name[i]]
    scan_args['field'] = p_scan_field_name[i]
    arglist += [(subms,scan_args['gaintable'],scan_args['gainfield'],scan_args),]
    
for arg in arglist:
    applycal_worker(arg[0],arg[1],arg[2],arg[3])

# flag secondary data
fmode = 'rflag'
dcol = 'corrected'
arglist = []
for i,scan in enumerate(p_scan):
    subms = get_subms(scan)
    arglist += [(subms,fmode,dcol),]
for arg in arglist:
    flagdata_worker(arg[0],arg[1],arg[2])

fmode = 'tfcrop'
dcol = 'corrected'
arglist = []
for i,scan in enumerate(p_scan):
    subms = get_subms(scan)
    arglist += [(subms,fmode,dcol),]
for arg in arglist:
    flagdata_worker(arg[0],arg[1],arg[2])
    
#----------------Round 3------------------
# Round 3
cround = 3

# Round 3, Gain cal on primary
caltype='G'
bptabc = gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(1)
gtabc = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(1)
ktabc = np.sort(glob.glob(gain_dir+'/cal_1GC_'+block_id+'*.'+'K'+str(cround-1))).tolist()[0]

gaintab = [ktabc,]+[gtabc,]+[bptabc]
cal_args = {'calmode':'ap',
            'minsnr':3,
            'interp':['nearest','nearest','nearest'],
            'gaintable':gaintab,
            'gainfield':np.repeat(strlist_to_str(np.unique(bp_scan_field_name)),len(gaintab)).tolist(),
            'field':strlist_to_str(np.unique(bp_scan_field_name).tolist()),
            'caltable':gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(cround),
           }

arg =  (mymms,caltype,cround,cal_args)
gaincal_worker(arg[0],arg[1],arg[2],arg[3])

# copy the calibration table to each secondary scan
for i,scan in enumerate(p_scan):
    caltable = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'G'+str(cround)
    primtable = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(cround)
    shutil.copytree(primtable,caltable)
    
#Round 3, gain on secondary
caltype='G'
#num_proc = min(len(p_scan),max_num_core)
bptabc = gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(1)
gtabc = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(1)
cal_args = {'calmode':'ap',
            'minsnr':3,
            'interp':('nearest','linear','linear'),
            
            'gainfield':[strlist_to_str(np.unique(bp_scan_field_name)),
                         strlist_to_str(np.unique(bp_scan_field_name)),
                         strlist_to_str(np.unique(bp_scan_field_name)),],
            'append':True,
           }
arglist = []
for i,scan in enumerate(p_scan):
    caltable = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'G'+str(cround)
    ktabc = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'K'+str(cround-1)
    scan_args = cal_args.copy()
    scanlist = strlist_to_str(np.sort(np.array(bp_scan+[scan],dtype='int')+1).astype('str').tolist())
    scan_args['scan'] = scanlist
    scan_args['field'] = p_scan_field_name[i]
    scan_args['caltable'] = caltable
    scan_args['gaintable']=[ktabc,gtabc,bptabc]
    arglist += [(mymms,caltype,cround,scan_args),]

for arg in arglist:
    gaincal_worker(arg[0],arg[1],arg[2],arg[3])

#copy the delay tables to secondary scans
for i,scan in enumerate(p_scan):
    caltable = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'K'+str(cround)
    primtable = gain_dir+'/cal_1GC_'+block_id+'.'+'K'+str(1)
    shutil.copytree(primtable,caltable)
    
#Round 3, delay on secondary
caltype='K'
#num_proc = min(len(p_scan),max_num_core)
bptabc = gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(1)
gtabc = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(1)
cal_args = {
            'interp':('linear','linear','linear'),
            'append':True,
           }

arglist = []
for i,scan in enumerate(p_scan):
    scan_args = cal_args.copy()
    gtabscan = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'G'+str(cround)
    scanlist = strlist_to_str(np.sort(np.array(bp_scan+[scan],dtype='int')+1).astype('str').tolist())
    scan_args['scan'] = scanlist
    scan_args['field'] = p_scan_field_name[i]
    scan_args['gaintable']=(gtabc,bptabc,gtabscan)
    scan_args['gainfield']=(strlist_to_str(np.unique(bp_scan_field_name)),strlist_to_str(np.unique(bp_scan_field_name)),p_scan_field_name[i])
    scan_args['field'] = p_scan_field_name[i]
    scan_args['caltable'] = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+caltype+str(cround)
    arglist += [(mymms,caltype,cround,scan_args),]
    
for arg in arglist:
    gaincal_worker(arg[0],arg[1],arg[2],arg[3])

#Round 3, flux scale on sec
caltype='flux'
#num_proc = min(len(p_scan),max_num_core)

cal_args = {
    #'reference':np.unique(bp_scan_field_name).tolist()[0]
    
    'reference':strlist_to_str(np.unique(bp_scan_field_name).tolist())
           }

arglist = []
for i,scan in enumerate(p_scan):
    scan_args = cal_args.copy()
    scanlist = strlist_to_str(np.sort(np.array(bp_scan+[scan],dtype='int')+1).astype('str').tolist())
    scan_args['scan'] = scanlist
    scan_args['caltable']=gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'G'+str(cround)
    scan_args['transfer']=p_scan_field_name[i]
    scan_args['fluxtable']=gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'flux'+str(cround)
    arglist+=[(mymms,cround,scan_args),]
    
for i,arg in enumerate(arglist):
    fluxscale_worker(arg[0],arg[1],arg[2])
    
# apply the solutions to the secondary
#num_proc = min(len(p_scan),max_num_core)
gtabc = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(1)
bptabc = gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(1)
app_args = {'interp':['nearest','linear','linear','linear'],
           }

arglist = []
for i,scan in enumerate(p_scan):
    ktabc = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'K'+str(cround)
    ftabc = gain_dir+'/cal_1GC_'+block_id+'_'+scan+'.'+'flux'+str(cround)
    subms = get_subms(scan)
    scan_args = app_args.copy()
    scan_args['gaintable'] = [ktabc,gtabc,bptabc,ftabc]
    scan_args['gainfield'] = ['','',strlist_to_str(np.unique(bp_scan_field_name)),p_scan_field_name[i]]
    scan_args['field'] = p_scan_field_name[i]
    arglist += [(subms,scan_args['gaintable'],scan_args['gainfield'],scan_args),]

for arg in arglist:
    applycal_worker(arg[0],arg[1],arg[2],arg[3])

# flag secondary data
fmode = 'rflag'
dcol = 'corrected'
arglist = []
for i,scan in enumerate(p_scan):
    subms = get_subms(scan)
    arglist += [(subms,fmode,dcol),]
    
for arg in arglist:
    flagdata_worker(arg[0],arg[1],arg[2])

fmode = 'tfcrop'
dcol = 'corrected'
arglist = []
for i,scan in enumerate(p_scan):
    subms = get_subms(scan)
    arglist += [(subms,fmode,dcol),]

for arg in arglist:
    flagdata_worker(arg[0],arg[1],arg[2])

    
# apply the solutions to the target scan
scan_list = ['%04i' % i for i in range(nscan)]
target_scan = [scan for scan in scan_list if scan not in g_scan]
scan = target_scan[0]
target_field = [field for field in CAL_1GC_FIELD_NAMES if field not in (CAL_1GC_PRIMARY_NAME+CAL_1GC_SECONDARY_NAME)][0]

gtabc = gain_dir+'/cal_1GC_'+block_id+'.'+'G'+str(1)
bptabc = gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(1)
app_args = {'interp':['nearest','linear','linear','linear'],
           }

arglist = []
for i,scan in enumerate(target_scan):
    pair_indx = np.argmin(np.abs(np.array(p_scan).astype('int')-int(scan)))
    pair_scan = p_scan[pair_indx]
    ktabc = gain_dir+'/cal_1GC_'+block_id+'_'+pair_scan+'.'+'K'+str(cround)
    ftabc = gain_dir+'/cal_1GC_'+block_id+'_'+pair_scan+'.'+'flux'+str(cround)
    subms = get_subms(scan)
    scan_args = app_args.copy()
    scan_args['gaintable'] = [ktabc,gtabc,bptabc,ftabc]
    scan_args['gainfield'] = ['',strlist_to_str(np.unique(bp_scan_field_name)),strlist_to_str(np.unique(bp_scan_field_name)),p_scan_field_name[pair_indx]]
    scan_args['field'] = target_field
    arglist += [(subms,scan_args['gaintable'],scan_args['gainfield'],scan_args),]

for arg in arglist:
    applycal_worker(arg[0],arg[1],arg[2],arg[3])
    
# flag target data
fmode = 'rflag'
dcol = 'corrected'
arglist = []
for i,scan in enumerate(target_scan):
    subms = get_subms(scan)
    arglist += [(subms,fmode,dcol),]

for arg in arglist:
    flagdata_worker(arg[0],arg[1],arg[2])
    
fmode = 'tfcrop'
dcol = 'corrected'
arglist = []
for i,scan in enumerate(target_scan):
    subms = get_subms(scan)
    arglist += [(subms,fmode,dcol),]

for arg in arglist:
    flagdata_worker(arg[0],arg[1],arg[2])
    

if save_flag:
    flagmanager(mymms, mode='save', versionname='after_1GC',)