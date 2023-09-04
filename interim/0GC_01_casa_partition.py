#mpicasa, LARGE, config.py
import glob
import sys
import os

config_file = sys.argv[-1]
execfile(config_file)
master_ms = FILE_master_ms
#master_ms = "/idia/raw/public/SCI-20180426-TM-01/1530399641/1530399641_sdp_l0.ms"

outms = FILE_working_ms
#outms = "/idia/projects/mightee/zchen/setjy_test/1530399641_sdp_l0_4096ch.mms"

partition(vis = master_ms,
	      outputvis = outms,
          createmms = True,
          separationaxis='scan', 
         )