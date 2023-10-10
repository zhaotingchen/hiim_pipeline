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
save_flag = (CAL_1GC_save_flag.lower()=='true')
use_field = (CAL_1GC_use_field_sources.lower()=='true')
data_dir = FILE_interim[:-7]+'data/'
temp_dir = OUTPUT_temp

if not use_field:
    print('only using the calibrator source')
    list_suffix = '_prim'
else:
    print('using the field sources')
    list_suffix = ''

syscall = ''
#python_file = 'import numpy as np \n' + 'from astropy.io import fits \n' + 'import os \n' + 'from casacore.tables import table \n'
python_file = '''
import numpy as np 
from astropy.io import fits 
from casacore.tables import table 
import pandas as pd
from astropy.wcs import WCS
from astropy.coordinates import Angle
from astropy import units as u
\n
'''

python_file += '''
mymms = '{mymms}'
spw_table = table(mymms+'/SPECTRAL_WINDOW',ack=False)
chans = spw_table.getcol('CHAN_FREQ')[0] 
deltav = np.diff(chans).mean()
\n
'''.format(**locals())

#python_file += '''
#def flux_model(nunu0,iref,coeffs,log=False):
#    if log:
#        exponent = np.sum([coeff*(np.log(nunu0)**(power))
#                       for power,coeff in enumerate(coeffs)],axis=0)
#        ifreq = iref*nunu0**exponent
#    else:
#        xarr = nunu0-1
#        polyterms = np.sum([coeff*((xarr)**(power+1))
#                       for power,coeff in enumerate(coeffs)],axis=0)
#        ifreq = iref+polyterms
#    return ifreq
#\n
#'''

channels_out = get_nchan(mymms)

for primary_name in CAL_1GC_PRIMARY_NAME:
    if ((primary_name != '1934-638')*(primary_name != '0408-65')):
        raise ValueError('Only support primary calibrator 1934-638 or 0408-65 currently')
    
    file_setup = dict(config['WSCLEAN_1GC']).copy()
    del file_setup['channels-out']
    field_id = np.where(np.array(CAL_1GC_FIELD_NAMES) == primary_name)[0][0]
    file_setup['name'] = OUTPUT_image+'/'+primary_name+'_dirty'
    file_setup['field'] = str(field_id)
    #file_setup['channels-out'] = str(channels_out)
    syscall += gen_syscall_wsclean(mymms,config,file_setup)
    
#    python_file += '''
#data = pd.read_csv('{FILE_interim}/../data/{primary_name}.txt',comment='#',header=None)
#data = data.values
#ra_list = data[:,2]
#dec_list = data[:,3]
#iref_list = ()
#freqref_list = ()
#coeff_list = ()
#for data_i in data:
#    iref_list += (float(data_i[4].split()[3]),)
#    freqref_list += (float(data_i[4].split()[-1]),)
#    coeff = data_i[4].split('[')[1].split(']')[0].split()
#    coeff = np.vectorize(float)(coeff).tolist()
#    coeff_list += (coeff,)
#freq_ref = freqref_list[0]
#im = fits.getdata('{OUTPUT_image}/{primary_name}_dirty-image.fits')
#header = fits.getheader('{OUTPUT_image}/{primary_name}_dirty-image.fits')
#im = np.zeros_like(im)
#wcs = WCS(header=header)
#sc_i = 0
#ra_sc = Angle(ra_list,unit=u.hour).to('deg').value
#ra_sc[ra_sc>180] = ra_sc[ra_sc>180]-360
#dec_sc = Angle(dec_list,unit=u.deg).to('deg').value
#x_indx,y_indx,_,_ = wcs.all_world2pix(ra_sc,dec_sc,header['CRVAL3'],1,0)
#x_indx = np.round(x_indx).astype('int')
#y_indx = np.round(y_indx).astype('int')
#flux_sc = np.zeros((len(x_indx),len(chans)))
#for sc_i in range(len(x_indx)):
#    flux_sc[sc_i] = flux_model(
#    chans/freq_ref,iref_list[sc_i],coeff_list[sc_i],log=False)
#for i in range({channels_out}):
#    outim = im.copy()
#    outim[0,0,x_indx,y_indx]+= flux_sc[:,i]
#    hdu = fits.PrimaryHDU(outim, header=header)
#    hdu.header['CRVAL3'] = chans[i]
#    hdu.writeto('/idia/projects/mightee/zchen/cal_test/IMAGES/{primary_name}_dirty-%04i-model.fits' %i)
#\n
#'''.format(**locals())
    python_file +='''
im = fits.getdata('{OUTPUT_image}/{primary_name}_dirty-image.fits')
header = fits.getheader('{OUTPUT_image}/{primary_name}_dirty-image.fits')
im = np.zeros_like(im)
for i in range({channels_out}):
    #im = fits.getdata('{OUTPUT_image}/{primary_name}_dirty-%04i-image.fits' %i)
    #header = fits.getheader('{OUTPUT_image}/{primary_name}_dirty-%04i-image.fits' %i)
    #im = np.zeros_like(im)
    hdu = fits.PrimaryHDU(im, header=header)
    hdu.header['CRVAL3'] = chans[i]
    hdu.header['CDELT3'] = deltav
    hdu.writeto('{OUTPUT_image}/{primary_name}_dirty-%04i-residual.fits' %i)
\n 
    '''.format(**locals())
    
jobname = '1GC_03_wsclean_predict'

with open(OUTPUT_script+'/'+'1GC_write_model_im.py','w') as f:
    f.write(python_file)

syscall_python = gen_syscall('container',OUTPUT_script+'/'+'1GC_write_model_im.py',config)

del file_setup['scale']
del file_setup['size']
del file_setup['niter']
del file_setup['auto-threshold']
del file_setup['no-update-model-required']
del file_setup['no-dirty']
del file_setup['field']
del file_setup['name']
#del file_setup['channels-out']
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
        infile = residual_file+' '+FILE_fieldsource+'/_'+primary_name+list_suffix+'.txt '+model_im
        syscall_restore += gen_syscall_wsclean(infile,config,file_setup)
    syscall_remove += 'rm '+OUTPUT_image+'/'+primary_name+'*residual.fits \n'
    syscall_remove += 'rm '+OUTPUT_image+'/'+primary_name+'*model.fits \n'
    predict_setup['name'] = OUTPUT_image+'/'+primary_name+'_dirty'
    predict_setup['field'] = str(field_id)
    syscall_predict += gen_syscall_wsclean(mymms,config,predict_setup)
    #for scan in CAL_1GC_PRIMARY_SCAN[prim_i]:
    #    subms = glob.glob(mymms+'/SUBMSS/*'+scan+'*.ms')[0]
    #    syscall_predict += gen_syscall_wsclean(subms,config,predict_setup)
        


job_handler(syscall+syscall_python+syscall_restore+syscall_predict+syscall_remove,jobname,config,'WSCLEAN')

        