#mpicasa, NODE, config.py, 0
import glob
import sys
import os
import numpy as np
import re

config_file = sys.argv[-1]
execfile(config_file)

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
    #clip zeros
    flagdata(vis = sub_ms,
         mode = 'clip',
         flagbackup=False,
         correlation='ABS_I',
         clipminmax = [1.01,50.0],
         datacolumn='model',
        )


#----------------Round 0------------------
cround = 0


# Round 0, delay on primary
caltype='K'
num_proc = len(bp_scan)

cal_args = {'uvrange':'',
            'field':strlist_to_str(np.unique(bp_scan_field_name)),
            'caltable':gain_dir+'/cal_1GC_'+block_id+'.'+caltype+str(cround)
           }
arg = (mymms,caltype,cround,cal_args)
gaincal_worker(arg[0],arg[1],arg[2],arg[3])

# round 0, phase only gain on primary
caltype='G'
num_proc = len(bp_scan)

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

#round 0, bandpass
caltype='B'
num_proc = len(bp_scan)

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


#Round 0, flag bandpass solutions
datacol = 'CPARAM'
fmode = 'tfcrop'
arg = (gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(cround),fmode,datacol)
flagdata_worker(arg[0],arg[1],arg[2])
datacol = 'CPARAM'
fmode = 'rflag'
arg = (gain_dir+'/cal_1GC_'+block_id+'.'+'B'+str(cround),fmode,datacol)
flagdata_worker(arg[0],arg[1],arg[2])

#Round 0, apply the solutions to the primary data
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

#Round 0, flag the vis data in prim scans
datacol = 'residual'
fmode = 'rflag'
flag_args = {'field':strlist_to_str(np.unique(bp_scan_field_name)),}
flagdata_worker(subms,fmode,datacol,flag_args)

datacol = 'residual'
fmode = 'tfcrop'
flagdata_worker(subms,fmode,datacol,flag_args)

#----------------Round 1------------------
cround=1
#Round 1, delay on prim
caltype='K'
num_proc = len(bp_scan)
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
num_proc = len(bp_scan)
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
num_proc = len(bp_scan)

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

#Round 1, flag the vis data in prim scans
datacol = 'residual'
fmode = 'rflag'
flag_args = {'field':strlist_to_str(np.unique(bp_scan_field_name)),}
flagdata_worker(subms,fmode,datacol,flag_args)

datacol = 'residual'
fmode = 'tfcrop'
flagdata_worker(subms,fmode,datacol,flag_args)

clearstat()
clearstat()