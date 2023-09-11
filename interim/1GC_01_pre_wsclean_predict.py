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
from hiimtool.config_util import gen_syscall_wsclean,job_handler,tidy_config_path,get_file_setup,find,gen_syscall
from hiimtool.ms_tool import get_nchan

config = tidy_config_path(config)

work_dir = config['FILE']['work_dir']
sys.path.append(work_dir)
from config import *


mymms = FILE_working_ms
save_flag = bool(CAL_1GC_save_flag)
use_field = bool(CAL_1GC_use_field_sources)
data_dir = FILE_interim[:-7]+'data/'
temp_dir = OUTPUT_temp

if not use_field:
    raise ValueError('use set_jy instead of this to ignore field sources')

syscall = ''
python_file = 'import numpy as np \n' + 'from astropy.io import fits \n' + 'import os \n' + 'from casacore.tables import table \n'
python_file += '''
mymms = '{mymms}'
spw_table = table(mymms+'/SPECTRAL_WINDOW',ack=False)
chans = spw_table.getcol('CHAN_FREQ')[0] \n
'''.format(**locals())

channels_out = get_nchan(mymms)

for primary_name in CAL_1GC_PRIMARY_NAME:
    if ((primary_name != '1934-638')*(primary_name != '0408-65')):
        raise ValueError('Only support primary calibrator 1934-638 or 0408-65 currently')
    
    file_setup = dict(config['WSCLEAN_1GC']).copy()
    del file_setup['channels-out']
    field_id = np.where(np.array(CAL_1GC_FIELD_NAMES) == primary_name)[0][0]
    file_setup['name'] = OUTPUT_image+'/'+primary_name+'_dirty'
    file_setup['field'] = str(field_id)
    syscall += gen_syscall_wsclean(mymms,config,file_setup)
    
    python_file +='''
im = fits.getdata('{OUTPUT_image}/{primary_name}_dirty-image.fits')
header = fits.getheader('{OUTPUT_image}/{primary_name}_dirty-image.fits')
im = np.zeros_like(im)
hdu = fits.PrimaryHDU(im, header=header)
for i in range(972):
    hdu = fits.PrimaryHDU(im, header=header)
    hdu.header['CRVAL3'] = chans[i]
    hdu.writeto('{OUTPUT_image}/{primary_name}_dirty-%04i-residual.fits' %i)
\n 
    '''.format(**locals())
    
jobname = '1GC_01_wsclean_predict'

with open(OUTPUT_script+'/'+'1GC_zero_residual.py','w') as f:
    f.write(python_file)

syscall_python = gen_syscall('container',OUTPUT_script+'/'+'1GC_zero_residual.py',config)

del file_setup['scale']
del file_setup['size']
del file_setup['niter']
del file_setup['auto-threshold']
del file_setup['no-update-model-required']
del file_setup['no-dirty']
del file_setup['field']
del file_setup['name']
predict_setup = file_setup.copy()
predict_setup['channels-out'] = str(channels_out)
file_setup['restore-list'] = ''

predict_setup['predict'] = ''

syscall_restore = '\n'
syscall_remove = ''
syscall_predict = ''
for prim_i,primary_name in enumerate(CAL_1GC_PRIMARY_NAME):
    field_id = np.where(np.array(CAL_1GC_FIELD_NAMES) == primary_name)[0][0]
    for i in range(channels_out):
        residual_file = OUTPUT_image+'/'+primary_name+'_dirty-%04i-residual.fits' %i
        model_im = OUTPUT_image+'/'+primary_name+'_dirty-%04i-model.fits' %i
        infile = residual_file+' '+FILE_fieldsource+'/'+primary_name+'.txt '+model_im
        syscall_restore += gen_syscall_wsclean(infile,config,file_setup)
    syscall_remove += 'rm '+OUTPUT_image+'/'+primary_name+'*residual.fits \n'
    predict_setup['name'] = OUTPUT_image+'/'+primary_name+'_dirty'
    predict_setup['field'] = str(field_id)
    syscall_predict += gen_syscall_wsclean(mymms,config,predict_setup)
    #for scan in CAL_1GC_PRIMARY_SCAN[prim_i]:
    #    subms = glob.glob(mymms+'/SUBMSS/*'+scan+'*.ms')[0]
    #    syscall_predict += gen_syscall_wsclean(subms,config,predict_setup)
        


job_handler(syscall+syscall_python+syscall_restore+syscall_remove+syscall_predict,jobname,config,'WSCLEAN')

        