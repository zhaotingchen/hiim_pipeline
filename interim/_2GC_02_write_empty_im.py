#container, BASIC, config.ini, 0
import glob
import sys
import os
import numpy as np
import configparser
from astropy.io import fits 
from casacore.tables import table 
import pandas as pd
from astropy.wcs import WCS
from astropy.coordinates import Angle


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
spw_table = table(mymms+'/SPECTRAL_WINDOW',ack=False)
chans = spw_table.getcol('CHAN_FREQ')[0] 
deltav = np.diff(chans).mean()
target_field = [field for field in CAL_1GC_FIELD_NAMES if field not in (CAL_1GC_PRIMARY_NAME+CAL_1GC_SECONDARY_NAME)][0]

imname = glob.glob(OUTPUT_image+'/'+target_field+'*image*fits')[0]
im = fits.getdata(imname)
header = fits.getheader(imname)
im = np.zeros_like(im)
for i in range(len(chans)):
    hdu = fits.PrimaryHDU(im, header=header)
    hdu.header['CRVAL3'] = chans[i]
    hdu.header['CDELT3'] = deltav
    hdu.writeto(('{OUTPUT_temp}/{target_field}_predict-%04i-residual.fits' %i).format(**locals()))